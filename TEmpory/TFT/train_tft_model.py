import os
import sys
try:
    import pkg_resources
except ImportError:
    class DummyPkgResources:
        @staticmethod
        def declare_namespace(name):
            pass
    sys.modules["pkg_resources"] = DummyPkgResources()
import torch
import lightning.pytorch as pl
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
from tft_dataset_builder import load_and_prepare_data, create_tft_dataset

def train_model():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.abspath(os.path.join(current_dir, '../../weather_data.db'))
    
    print("1. Loading Data...")
    df = load_and_prepare_data(db_path)
    
    print("2. Building TimeSeriesDataSet...")
    # Using 24 hours of lookback to predict 1 hour ahead for better accuracy
    training_dataset = create_tft_dataset(df, max_encoder_length=24, max_prediction_length=1)
    
    # Create a small validation set
    validation_dataset = TimeSeriesDataSet.from_dataset(training_dataset, df, predict=True, stop_randomization=True)
    
    # Optimized for Apple M1 Pro (Increased batch size and worker threads)
    batch_size = 256 
    train_dataloader = training_dataset.to_dataloader(train=True, batch_size=batch_size, num_workers=4, persistent_workers=True)
    val_dataloader = validation_dataset.to_dataloader(train=False, batch_size=batch_size * 2, num_workers=4, persistent_workers=True)
    
    print("3. Defining TFT Model...")
    tft = TemporalFusionTransformer.from_dataset(
        training_dataset,
        learning_rate=0.03,
        hidden_size=32,
        attention_head_size=2,
        dropout=0.15,
        hidden_continuous_size=16,
        output_size=1,  # Predict single value (wind speed)
        loss=pytorch_forecasting.metrics.MAE(),
        log_interval=10, 
        reduce_on_plateau_patience=4,
    )
    
    print(f"Number of parameters in network: {tft.size()/1e3:.1f}k")
    
    print("4. Configuring Trainer...")
    early_stop_callback = EarlyStopping(monitor="val_loss", min_delta=1e-4, patience=4, verbose=False, mode="min")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    trainer = pl.Trainer(
        max_epochs=20, # Increased for better training
        accelerator="auto", 
        enable_model_summary=True,
        gradient_clip_val=0.1,
        callbacks=[early_stop_callback],
        default_root_dir=current_dir
        # limit_train_batches=30, # Removed the limit so it trains on full data!
    )
    
    print("5. Starting Training (Full Training Mode)...")
    trainer.fit(
        tft,
        train_dataloaders=train_dataloader,
        val_dataloaders=val_dataloader,
    )
    
    print("--------------------------------------------------")
    print("Training Completed.")
    
    # Save the model
    best_model_path = trainer.checkpoint_callback.best_model_path
    best_val_loss = trainer.checkpoint_callback.best_model_score
    if best_model_path:
        print(f"Best model saved at: {best_model_path}")
        if best_val_loss is not None:
            # val_loss is the MAE (Mean Absolute Error) in Knots
            print(f"🌟 Final Model Accuracy (MAE): {best_val_loss.item():.2f} Knots error on average 🌟")
    else:
        print("No model checkpoint found (training might have been too short).")
    print("--------------------------------------------------")

if __name__ == "__main__":
    import pytorch_forecasting
    train_model()
