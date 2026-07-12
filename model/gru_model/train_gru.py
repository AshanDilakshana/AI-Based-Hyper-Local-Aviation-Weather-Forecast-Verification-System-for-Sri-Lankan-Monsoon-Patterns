import os
import joblib
import numpy as np
import pandas as pd
import keras_tuner as kt

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping


# ===============================
# PATH
# ===============================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_DIR = os.path.dirname(
    os.path.dirname(BASE_DIR)
)


DATA_PATH = os.path.join(
    PROJECT_DIR,
    "data",
    "featured_northeast_monsoon.csv"
)


# ===============================
# LOAD DATA
# ===============================

df = pd.read_csv(DATA_PATH)

print(df.shape)



# ===============================
# FEATURES
# ===============================

drop_cols = [
    "datetime",
    "future_time",
    "target_temperature",
    "target_pressure",
    "target_humidity"
]


X = df.drop(
    columns=drop_cols,
    errors="ignore"
)


y = df[
    [
        "target_temperature",
        "target_pressure"
    ]
]


X = X.select_dtypes(
    include=np.number
)


X = X.fillna(
    X.mean()
)


y = y.fillna(
    y.mean()
)



# ===============================
# SCALING
# ===============================


X_scaler = MinMaxScaler()

y_scaler = MinMaxScaler()


X_scaled = X_scaler.fit_transform(
    X
)


y_scaled = y_scaler.fit_transform(
    y
)




# ===============================
# SEQUENCE
# ===============================


TIME_STEPS = 48


def create_sequences(X,y):

    Xs=[]
    ys=[]


    for i in range(len(X)-TIME_STEPS):

        Xs.append(
            X[i:i+TIME_STEPS]
        )

        ys.append(
            y[i+TIME_STEPS]
        )


    return np.array(Xs),np.array(ys)



X_seq,y_seq = create_sequences(
    X_scaled,
    y_scaled
)



# split

split = int(
    len(X_seq)*0.8
)


X_train = X_seq[:split]
X_test = X_seq[split:]

y_train = y_seq[:split]
y_test = y_seq[split:]



# ===============================
# GRU BUILDER
# ===============================


def build_gru(hp):


    model = Sequential()


    model.add(
        GRU(

            units=hp.Choice(
                "gru1",
                [64,128,256]
            ),

            return_sequences=True,

            input_shape=(
                TIME_STEPS,
                X_train.shape[2]
            )

        )
    )


    model.add(
        BatchNormalization()
    )


    model.add(
        Dropout(
            hp.Choice(
                "dropout1",
                [0.2,0.3,0.5]
            )
        )
    )



    model.add(
        GRU(

            units=hp.Choice(
                "gru2",
                [32,64,128]
            )

        )
    )



    model.add(
        Dense(
            hp.Choice(
                "dense",
                [16,32,64]
            ),
            activation="relu"
        )
    )


    model.add(
        Dense(2)
    )



    model.compile(

        optimizer=Adam(

            learning_rate=hp.Choice(

                "learning_rate",

                [
                    0.001,
                    0.0005,
                    0.0001
                ]

            )

        ),

        loss="mse",

        metrics=["mae"]

    )


    return model




# ===============================
# TUNING
# ===============================


tuner = kt.RandomSearch(

    build_gru,

    objective="val_loss",

    max_trials=20,

    executions_per_trial=1,

    directory="gru_tuning",

    project_name="weather_model"

)



tuner.search(

    X_train,

    y_train,

    epochs=100,

    validation_split=0.2,

    batch_size=32

)



# ===============================
# BEST MODEL
# ===============================


best_model = tuner.get_best_models(
    num_models=1
)[0]


best_hp = tuner.get_best_hyperparameters(
    1
)[0]


print("\nBEST PARAMETERS")

print(
    best_hp.values
)



# ===============================
# FINAL TRAINING
# ===============================


early_stop = EarlyStopping(

    patience=20,

    restore_best_weights=True

)



best_model.fit(

    X_train,

    y_train,

    epochs=300,

    batch_size=32,

    validation_split=0.2,

    callbacks=[
        early_stop
    ]

)



# ===============================
# TEST
# ===============================


pred_scaled = best_model.predict(
    X_test
)


pred = y_scaler.inverse_transform(
    pred_scaled
)


actual = y_scaler.inverse_transform(
    y_test
)



r2 = r2_score(
    actual,
    pred
)



print("\nGRU PERFORMANCE")

print(
    "Temperature MAE:",
    mean_absolute_error(
        actual[:,0],
        pred[:,0]
    )
)


print(
    "Pressure MAE:",
    mean_absolute_error(
        actual[:,1],
        pred[:,1]
    )
)


print(
    "RMSE:",
    np.sqrt(
        mean_squared_error(
            actual,
            pred
        )
    )
)


print(
    "R2:",
    r2
)


print(
    "Accuracy:",
    round(r2*100,2),
    "%"
)



# SAVE

best_model.save(
    os.path.join(
        BASE_DIR,
        "best_gru_weather_model.keras"
    )
)


joblib.dump(
    X_scaler,
    os.path.join(
        BASE_DIR,
        "X_scaler.pkl"
    )
)


joblib.dump(
    y_scaler,
    os.path.join(
        BASE_DIR,
        "y_scaler.pkl"
    )
)


print("✅ Tuned GRU Saved")