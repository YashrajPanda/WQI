from fastapi import FastAPI
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from datetime import timedelta
import base64
import io
import logging
from matplotlib.image import imsave

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Water Quality Backend")

def generate_data():
    try:
        dates = pd.date_range(end=pd.Timestamp.today().floor('D'), periods=30)
        pH = np.random.normal(7.0, 0.2, 30)
        DO = np.random.normal(8.0, 0.4, 30)
        rainfall = np.random.exponential(5, 30)
        fecal_coliform = np.random.lognormal(3.0, 0.4, 30).clip(100, 1000) + (rainfall * 0.5)

        historical_data = pd.DataFrame({
            'date': dates,
            'pH': pH,
            'DO': DO,
            'rainfall': rainfall,
            'fecal_coliform': fecal_coliform
        }).set_index('date')

        last_fecal = historical_data['fecal_coliform'].iloc[-1]
        trend = np.mean(historical_data['fecal_coliform'].diff().dropna())
        forecast_dates = [dates[-1] + timedelta(days=i+1) for i in range(3)]
        forecast_fecal = [last_fecal + trend * (i + 1) for i in range(3)]
        forecast_data = pd.DataFrame({
            'date': forecast_dates,
            'forecast_fecal': forecast_fecal
        }).set_index('date')

        latest_fecal = historical_data['fecal_coliform'].iloc[-1]
        image = np.zeros((50, 50, 3))
        if latest_fecal < 400:
            image[:, :, 1] = 1.0
        elif latest_fecal < 800:
            image[:, :, 0] = 1.0
            image[:, :, 1] = 1.0
        else:
            image[:, :, 0] = 1.0

        buffer = io.BytesIO()
        imsave(buffer, image, format='png')
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return {
            "historical_data": historical_data.reset_index().to_dict(orient='records'),
            "forecast_data": forecast_data.reset_index().to_dict(orient='records'),
            "satellite_image_base64": image_base64,
            "latest_fecal": latest_fecal
        }
    except Exception as e:
        logger.error(f"Error in generate_data: {str(e)}")
        raise

@app.get("/data")
def get_water_quality_data():
    try:
        data = generate_data()
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Error in /data endpoint: {str(e)}")
        return JSONResponse(
            content={"error": f"Internal Server Error: {str(e)}"},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)