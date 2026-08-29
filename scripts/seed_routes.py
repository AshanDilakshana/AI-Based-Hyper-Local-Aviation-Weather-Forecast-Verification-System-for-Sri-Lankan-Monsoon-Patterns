import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

from backend.data.database import engine, Base, SessionLocal
from backend.data.models import RouteAlternatives

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

regions_data = {
    "India": "VCBI VOMM VOTV VOTR VOCL VOBG VOBL VRMM VRMG VAAH VABB VIDP VIBN VILK VNKT OPKC OPLA VGHS VOMD VOHS VOCI",
    "Middle East": "VCBI VOMM VOCI VRMM VABB OMAA OMAL OMDB OMSJ OKBK OEDR OERK OEJN OTBD OOMS OOSA OBBI OJAM OJAI OIII VOTV OPLA OPRN OPKC UUDD OMAD OMDW OMRK",
    "Sin": "VCBI VOMM VOCI VOPB VTBD VTBS VTBU VTCC VTSP VGZR VLVT VYYY WSSS WSAP WIHH WIMM WMKJ WMKP WMSA WMKL WITT WIDD WMKK WADD WIIH WIII ZPPP ZGNN ZGGG ZSSS RCTP ZBAA ZSPD VHHH ZGSZ",
    "Europe": "EGKK EGLL EGSS EGPK EBBR EHAM EDDF LFPO LFPG LOWW LSZH LIMC LDZA LTBA LGAT OIII EDDM EDDL EDDS EDDT EDDH OISS OITT LIRF LIRA LIMG LMML HECA HEAX LFMN LIMF LIVP LIBR EBBS ELLX UKBB LFPB UUDD UUEE NWWW",
    "Charles Paris": "LFPG LFPO LFMN LSGG LSZH LIMC LYZAGAT EBBR",
    "Leanado Italy": "LIRF LIBR LIRP LIMC LFMN LGAT LTBA",
    "Heatrow London": "EGLL EGKK EGSS EGPK EBBR LFPO LFPG EHAM EDDF LOWW LSZH LIMC LYZA LTBA LGAT",
    "Germany": "EDDF EDDM EDDL EDDS EDDT EDDH EDDK EDDN LOWW LHBA LYZA LGAT LTBA",
    "Gatwik London": "EGKK EGLL EGSS EGPK EBBR LFPO LFPG EHAM EDDF LOWW LSZH LIMC LYZA LTBA LGAT",
    "Japan": "RJFF RJAA RJTT RJNN RJOO RCTP RCKH VHHH ZGGG ZSSS ZHSC ZGKL RKSS RKPC VECC VTCC RKSI ROIG RCSS",
    "Africa": "FMMI HECA HTDA FJDG HFFF HUEN FAJS HELX FQMA FIMP HCMM HKMO HKNA FSIA DNAA",
    "Russia": "VCBI VOMM VOCI VRMM VABB UUDD UUEE UUWW UIUU UIBB UIII EFTU OMAA OMAL OMDB OMSJ OKBK OTBD OEDR OERK OEJN OEDF OOMS OOSA OBBI OJAM OJAI OIII VOTV OPLA OPRN OPKC HSSS FOOL UUDD VAAH LLBG",
    "Australia": "YMML YSSY YMHB YBBN YPPH YPAD YPCC LTBA LOWW LSZH LIMC LYZA LGAT EGKK EGLL EGSS EGPK EBBR LFPO LFPG EHAM EDDF"
}

for name, codes in regions_data.items():
    existing = db.query(RouteAlternatives).filter(RouteAlternatives.region_name == name).first()
    if not existing:
        new_route = RouteAlternatives(region_name=name, airports=codes)
        db.add(new_route)
    else:
        existing.airports = codes
        
db.commit()
print("Seeding completed.")
