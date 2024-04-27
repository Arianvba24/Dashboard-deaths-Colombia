import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime
from streamlit_folium import st_folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
import folium




def obtener_coordenadas(ciudad,pais):
    try:
        
        geolocalizador = Nominatim(user_agent="mi_app")
        ubicacion = geolocalizador.geocode(ciudad + ','+ pais)

        if ubicacion:
            latitud = ubicacion.latitude
            longitud = ubicacion.longitude
            return latitud, longitud
        else:
            return None
    except:
        
        return "Error", "Error"

def main():
    st.set_page_config(page_title="Dashboard muertes colombia",layout="wide")
    valores = st.sidebar.selectbox("Menu",["Dashboard","About"])
    
    path = r"raw_data.parquet"
    df = pd.read_parquet(path)
    df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"],format="%d/%m/%Y")
    df["Año"] = df["fecha_hecho"].dt.year

    

    valores_genero = {"NO REPORTA":"NO REPORTADO","-":"NO REPORTADO"}
    valores_grupo_etario = {"NO REPORTA":"NO REPORTADO"}
    
    df["grupo_etario"] = df["grupo_etario"].replace(valores_grupo_etario)
    df["genero"] = df["genero"].replace(valores_genero)

    genero = st.sidebar.multiselect("Elegir genero",df["genero"].unique())
    rango_edad = st.sidebar.multiselect("Elegir rango edad",df["grupo_etario"].unique())

    def buscar_genero(x):
        if x in genero:
            return True
        else:
            return False

    def buscar_rango_edad(x):
        if x in rango_edad:
            return True
        else:
            return False


    df = df.loc[
        (df["genero"].apply(buscar_genero)==True) &
        (df["grupo_etario"].apply(buscar_rango_edad)==True)
        
        
        ]

        


    if valores == "Dashboard":
        

        st.title("Muertes por violencia doméstica en Colombia desde el año 2010")

        if len(genero) > 0 and len(rango_edad) > 0:
            
    
            col1,col2,col3,col4 = st.columns([2,2,2,3])

            
            

            with col4:
                fecha_1 = st.date_input("Fecha inicial",format="DD/MM/YYYY",min_value=df["fecha_hecho"].min(),max_value=df["fecha_hecho"].max(),value=df["fecha_hecho"].max())
                fecha_2 = st.date_input("Fecha final",format="DD/MM/YYYY",min_value=df["fecha_hecho"].min(),max_value=df["fecha_hecho"].max(),value=df["fecha_hecho"].max())
                
                fecha_inicial = fecha_1.strftime("%d-%m-%Y")
                fecha_final = fecha_2.strftime("%d-%m-%Y")

                df = df.loc[
                    (df["fecha_hecho"] >= fecha_inicial) &
                    (df["fecha_hecho"] <= fecha_final)
                    ]
                
            personas = df["cantidad"].sum()
            hombres = df.loc[df["genero"]=="MASCULINO","cantidad"].sum()
            mujeres = df.loc[df["genero"]=="FEMENINO","cantidad"].sum()
            no_reportadas = df.loc[df["genero"]=="NO REPORTADO","cantidad"].sum()

            with col1:

                st.metric("Personas asesinadas",f"{personas}")
                st.metric("No reportadas asesinadas",no_reportadas)

            with col2:

                st.metric("Mujeres asesinadas",mujeres)

            with col3:

                st.metric("Hombres asesinados",hombres)


            tab1,tab2 = st.tabs(["General","Máximo y mínimo"])

            with tab1:
                col1,col2 = st.columns([2.8,3])
                with col1:


                    dl = pd.pivot_table(df,index="genero",values="cantidad",aggfunc="sum",fill_value=0).reset_index()

                    
                
                    fig2 = go.Figure()

                    fig2.add_trace(go.Pie(labels=dl["genero"].values,values=dl["cantidad"].values))
                                        

                    st.plotly_chart(fig2)





                    dp = pd.pivot_table(df,index="Año",columns="genero",values="cantidad",aggfunc="sum",fill_value=0).reset_index()
               
                    dp["Año"]=dp["Año"].astype(str)

                    columns = dp.columns.to_list()

                    

                    fig2 = go.Figure()

                    for column in columns[1:]:
                        fig2.add_trace(go.Line(x=dp[columns[0]].values,y=dp[column].values,name=column,mode="lines"
                                        ))
                        
                    st.plotly_chart(fig2)

                with col2:
                    dp = pd.pivot_table(df,index="Año",columns="genero",values="cantidad",aggfunc="sum",fill_value=0).reset_index()
                    # dp["valores"] = dp["NO REPORTADO"] + dp["NO REPORTA"] + dp["-"]
                    # dp.drop(columns=["-","NO REPORTA","NO REPORTADO"],inplace=True)
                    # dp.rename(columns={"valores":"NO REPORTADO"},inplace=True)
                    dp["Año"]=dp["Año"].astype(str)
                    columns = dp.columns.to_list()
                    fig = go.Figure()

                    for column in columns[1:]:
                        fig.add_trace(go.Bar(x=dp[columns[0]].values,y=dp[column].values,name=column
                                        ))
                    st.plotly_chart(fig)

                    columns = dp.columns.to_list()

                    fig2 = go.Figure()

                    fig2.add_trace(go.Table(header={"values":columns,"fill_color":'lightblue'},cells = {"values":[dp[x].values for x in columns]}))

                    st.plotly_chart(fig2)

                with st.expander("Mapas"):
                    st.markdown("#### Crear los mapas llevará unos segundos ya que al no tener coordenadas usamos Geopy para obtenerlas")
                    st.markdown("#### ¿Desea continuar?")
                    aceptar = st.button("Generar mapa")

                    if aceptar:

                

                    # if st.session_state.load_state:
                    #     st.session_state.load_state = True
                    
                        
                    
                        def crear_mapa():

                        
                            dx = pd.pivot_table(df,index=["departamento","municipio"],values="cantidad",aggfunc="sum")

                            dx = dx.reset_index()

                            def ordenar(x):
                                return [(x,c) for x,c in zip(x["municipio"],x["cantidad"])]
                                
                            dx = dx.groupby(["departamento"]).apply(ordenar).reset_index()    
                            # Crear coordenadas
                            valores = dx["departamento"].values
                            coordenadas = [obtener_coordenadas(x,"Colombia") for x in valores]
                            lat = []
                            long = []

                            for coordenada in coordenadas:
                                try:
                                    lat.append(coordenada[0])
                                    long.append(coordenada[1])
                                except:
                                    lat.append("Error")
                                    long.append("Error")

                            # Despues de crear las coordenadas
                            dx["lat"] = lat
                            dx["long"] = long

                            dx.rename(columns={0:"cantidad"},inplace=True)
                            
                            

                            m = folium.Map(location=(4.6529539, -74.0835643),tiles="Cartodb Positron",zoom_start=6)


                            numero = 14    
                            for valor in dx.iterrows():
                                try:
                                    values = {
                                        "Ciudad" : [x[0] for x in valor[1][1]],
                                        "Cantidad" : [x[1] for x in valor[1][1]]
                                        
                                    }
                                    df_html = pd.DataFrame(values).sort_values(by="Cantidad",ascending=False).to_html(
                                    classes="table table-striped table-hover table-condensed table-responsive")
                                    marker = folium.Circle(location=[valor[1][2],valor[1][3]],
                                                    radius=40000,
                                                    color="cornflowerblue",
                                                    stroke=False,
                                                    fill=True,
                                                    fill_opacity=0.6,
                                                    opacity=1,
                            #                        
                                                    popup= folium.Popup(df_html)    
                                                    ).add_to(m)
                                
                                except:
                                    pass
                            folium_static(m,width=1025)

                        crear_mapa()
                    
                    # folium_static(crear_mapa(),width=1025,)

                    # if aceptar == "Si":
                    #     crear_mapa()

                  
                    

            # import folium
            # from folium.plugins import MarkerCluster
            # # Crear un mapa
            # m = folium.Map(location=[40.7128, -74.0060], zoom_start=10)

            # # Crear un objeto MarkerCluster
            # marker_cluster = MarkerCluster().add_to(m)

            # # Agregar marcadores al MarkerCluster
            # for lat, lon in [(40.7128, -74.0060), (40.7128, -74.0070), (40.7138, -74.0060)]:
            #     folium.Marker(location=[lat, lon]).add_to(marker_cluster)
            # # Mostrar el mapa
            
            # st_folium(m,width=1025)


    
            with tab2:
                
                col1,col2 = st.columns([3,3])

                with col1:
                    dx = pd.pivot_table(df,index="genero",values = "cantidad",aggfunc="sum",fill_value=0).reset_index()
                    def colores(x):
                        if x["cantidad"] == dx["cantidad"].max():
                            return 'crimson'
                        else:
                            return "lightslategray"
                        
                    def posicion(x):
                        if x["cantidad"] == dx["cantidad"].max():
                            return 0.2
                        else:
                            return 0
                        

                    dx["colores"] = dx.apply(colores,axis=1)
                    dx["posicion"] = dx.apply(posicion,axis=1)
                    colors = dx["colores"].values
                    fig = go.Figure()

                    fig.add_trace(go.Pie(labels=dx["genero"].values,values=dx["cantidad"].values,
                                    marker_colors=colors,pull=dx["posicion"].values))

                    st.plotly_chart(fig)

                with col2:
                    dj= pd.pivot_table(df,index="Año",values = "cantidad",aggfunc="sum",fill_value=0).reset_index()

                    def colores(x):
                        if x["cantidad"] == dj["cantidad"].max():
                            return 'crimson'
                        else:
                            return "lightslategray"

                    dj["colores"] = dj.apply(colores,axis=1)

                    dj["Año"] = dj["Año"].astype(str)
                    fig = go.Figure()
                    colores = dj["colores"].values
                    fig.add_trace(go.Bar(y=dj["cantidad"].values,x=dj["Año"].values,marker_color=colores))
                    st.plotly_chart(fig)
                    







        


    elif valores == "About":
        st.title("Sobre el gráfico de muertes...")
        texto = "### El gráfico que se muestra en esta aplicación muestra la cantidad de muertes por violencia doméstica en Colombia ocurridos entre el año "
        texto1 ="2010 y 2023. Y podemos observar los diferentes análisis que se llevan a cabo." 
        st.markdown(texto + texto1)
       




 
    








if __name__=="__main__":
    main()
