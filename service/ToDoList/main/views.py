import pandas as pd
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
import joblib
import os
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.forms import UserChangeForm
from .forms import EditProfileForm
from django.contrib.auth import update_session_auth_hash

def home(request):
    return render(request, 'main/home.html')

def about(request):
    return render(request, 'main/about.html')

def services(request):
    return render(request, 'main/services.html')

def contact(request):
    return render(request, 'main/contact.html') 

def waterlevel(request):
    return render(request, 'waterlevel/waterlevel.html') 

def detect(request):
    return render(request, 'detect/home.html') 

def create_geojson(features):
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    return geojson

def create_polygon_feature(lat, lng, fill_color, fill_opacity=0.2, stroke_color=None, stroke_opacity=0, stroke_weight=2):
    if stroke_color is None:
        stroke_color = fill_color
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [lng - 0.001, lat - 0.001],
                [lng - 0.001, lat + 0.001],
                [lng + 0.001, lat + 0.001],
                [lng + 0.001, lat - 0.001],
                [lng - 0.001, lat - 0.001]
            ]]
        },
        "properties": {
            "fillColor": fill_color,
            "fillOpacity": fill_opacity,
            "strokeColor": stroke_color,
            "strokeOpacity": stroke_opacity,
            "strokeWeight": stroke_weight
        }
    }
    return feature

def create_point_feature(lat, lng, title, address, capacity, region, marker_color="#FF0000"):
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lng, lat]
        },
        "properties": {
            "markerColor": marker_color,
            "markerSize": "medium",
            "markerSymbol": "circle",
            "title": title,
            "address": address,
            "capacity": capacity,
            "region": region
        }
    }
    return feature

def get_geojson_data():
    csv_file_name3 = 'df.csv'
    excel_file_name = '광주광역시-침수피해현황_20231018.xlsx'
    excel_file_name2 = '광주광역시_대피소.xlsx'
    
    csv_file_path3 = os.path.join(settings.DATA_DIR, csv_file_name3)
    excel_file_path = os.path.join(settings.DATA_DIR, excel_file_name)
    excel_file_path2 = os.path.join(settings.DATA_DIR, excel_file_name2)
    
    df3 = pd.read_excel(excel_file_path) 
    df2 = pd.read_excel(excel_file_path2) 
    df = pd.read_csv(csv_file_path3)

    lat_column = 'Latitude'
    lng_column = 'Longitude'
    shelter_name_column = '대피소 명칭'
    address_column = '주소'
    capacity_column = '최대 수용 인원'
    region_column = '구'
    
    features = []
    
    for index, row in df3.iterrows():
        lat = row[lat_column]
        lng = row[lng_column]
        if pd.notnull(lat) and pd.notnull(lng):
            features.append(create_polygon_feature(lat, lng, fill_color="#FF0000"))
    
    for index, row in df.iterrows():
        lat = row[lat_column]
        lng = row[lng_column]
        if pd.notnull(lat) and pd.notnull(lng):
            features.append(create_polygon_feature(lat, lng, fill_color="#0000FF"))

    for index, row in df2.iterrows():
        lat = row[lat_column]
        lng = row[lng_column]
        shelter_name = row[shelter_name_column]
        address = row[address_column]
        capacity = row[capacity_column]
        region = row[region_column]
        if pd.notnull(lat) and pd.notnull(lng):
            features.append(create_point_feature(lat, lng, shelter_name, address, capacity, region))
            
    return create_geojson(features)

def map_data_view(request):
    geojson_data = get_geojson_data()
    return JsonResponse(geojson_data)

def map_view(request):
    return render(request, 'main/base.html')

def handle_button(request):
    button_value = request.GET.get('button_value')
    if button_value is not None:
        model_path = os.path.join(settings.DATA_DIR, 'model.pkl')

        road_csv_path = os.path.join(settings.DATA_DIR, '광주_도로명_샘플.csv')
        model = joblib.load(model_path)
        
        road_csv = pd.read_csv(road_csv_path)
        road_csv['강수량'] = int(button_value)
        road_csv1 = road_csv.drop(['시도시군구'], axis=1)
        
        pred = model.predict(road_csv1)
        y_score = (pred > 0.8).astype(int)
        df = road_csv[['Latitude', 'Longitude']][y_score.astype(bool)]
        print(df)
        features = []
        
        for _, row in df.iterrows():
            lat = row['Latitude']
            lng = row['Longitude']
            if pd.notnull(lat) and pd.notnull(lng):
                features.append(create_polygon_feature(lat, lng, fill_color="#0000FF"))
        
        return JsonResponse(create_geojson(features))
    
    return JsonResponse({'error': 'No value provided'}, status=400)

@login_required
def profile(request):
    return render(request, 'main/profile.html')

@login_required
def delete_account(request):
    user = request.user
    user.delete()
    logout(request)
    return redirect('home')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)  # 비밀번호 변경 후 세션 유지
            return redirect('profile')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'main/edit_profile.html', {'form': form})