import requests
import pandas as pd
import os

def download_hourly_GHI(lat, lon, year, city_name):
    base_url = "https://power.larc.nasa.gov/api/temporal/hourly/point"
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": f"{year}0101",
        "end": f"{year}1231",
        "format": "JSON"
    }

    print(f"\nRequesting hourly GHI for {city_name} ({lat}, {lon}) in {year} ...")
    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        print(f"❌ HTTP error {response.status_code}")
        return

    data = response.json()
    try:
        ghi = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    except KeyError:
        print("❌ No GHI data returned by NASA.")
        return

    # convert to dataframe
    df = pd.DataFrame(list(ghi.items()), columns=["DateTime", "GHI_Wm2"])
    df["DateTime"] = pd.to_datetime(df["DateTime"], format="%Y%m%d%H")

    # split datetime
    df["Year"] = df["DateTime"].dt.year
    df["Month"] = df["DateTime"].dt.month
    df["Day"] = df["DateTime"].dt.day
    df["Hour_decimal"] = df["DateTime"].dt.hour + df["DateTime"].dt.minute / 60

    # convert to kWh/m²
    df["GHI_kWhm2"] = df["GHI_Wm2"] / 1000.0

    # reorder columns
    df = df[["Year", "Month", "Day", "Hour_decimal", "GHI_kWhm2"]]

    # ---- ORIGINAL MONTHLY + YEARLY STATISTICS ----
    print("\n📊 Monthly average hourly GHI (kWh/m² per hour):")
    monthly_avg = df.groupby("Month")["GHI_kWhm2"].mean()

    print("\n📈 Monthly total GHI (kWh/m² per month):")
    monthly_sum = df.groupby("Month")["GHI_kWhm2"].sum()

    for m in range(1, 12 + 1):
        if m in monthly_avg.index:
            print(f"  Month {m:02}:  Avg = {monthly_avg[m]:.4f}   Total = {monthly_sum[m]:.2f}")
        else:
            print(f"  Month {m:02}: No data")

    yearly_avg = df["GHI_kWhm2"].mean()
    yearly_sum = df["GHI_kWhm2"].sum()

    print(f"\n🌞 Full-year average hourly GHI: {yearly_avg:.4f} kWh/m² per hour")
    print(f"🌞 Full-year total GHI: {yearly_sum:.2f} kWh/m² per year")

    # --------------------------------------------------------------
    # ✅ NEW PART: MONTHLY AVERAGE DAILY GHI (kWh/m²/day)
    # --------------------------------------------------------------

    print("\n🌤 Global horizontal irradiation (kWh/m²/day):\n")

    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # compute daily sums
    daily_ghi = df.groupby(["Year", "Month", "Day"])["GHI_kWhm2"].sum()

    # compute monthly average daily GHI
    monthly_avg_daily = daily_ghi.groupby("Month").mean()

    # yearly average daily GHI
    yearly_avg_daily = daily_ghi.mean()

    # print results
    for m in range(1, 13):
        if m in monthly_avg_daily.index:
            print(f"{month_names[m-1]:<10} {monthly_avg_daily[m]:.2f}")
        else:
            print(f"{month_names[m-1]:<10} No data")

    print(f"\nYear      {yearly_avg_daily:.2f}")

    # --------------------------------------------------------------

    # Save to Excel
    os.makedirs("ghi_output", exist_ok=True)
    file_name = f"ghi_output/{city_name.lower().replace(' ', '_')}_{year}_GHI.xlsx"
    df.to_excel(file_name, index=False)

    print(f"\n✅ Excel file saved as: {file_name}")
    print(f"📈 Total hourly records: {len(df)}")


if __name__ == "__main__":
    city = input("Enter location name (e.g. Ho Chi Minh): ")
    lat = float(input("Enter latitude (e.g. 10.8): "))
    lon = float(input("Enter longitude (e.g. 106.7): "))
    year = input("Enter year (e.g. 2024): ")

    download_hourly_GHI(lat, lon, year, city)
