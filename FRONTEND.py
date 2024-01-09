#----------IMPORT PACKAGE----------
import streamlit as st
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import harmonica as hm
import xarray as xr
from io import BytesIO
import folium
from folium.raster_layers import ImageOverlay


#----------SET PAGE CONFIG----------
st.set_page_config(layout='wide',page_title="Geophysics Visualization", page_icon=":mag:")


st.title("Geophysics Data Visualization")
page = st.sidebar.selectbox("METHOD", ("Magnetic","Gravity"))
#---------------------END PAGE CONFIG--------------------------

#----------DATA INPUT----------
st.sidebar.header("Data Input")
uploaded_file = st.sidebar.file_uploader("Upload CSV or TXT file", type=["csv", "txt"])

data = None

#----------CEK DATA IS UPLOADED----------
if page == "Magnetic":
    if uploaded_file is not None:
        # Read data from uploaded file
        if uploaded_file.type == "text/plain":
            data = pd.read_csv(uploaded_file, header=None, delim_whitespace=True, names=['Latitude', 'Longitude', 'TMI'],skiprows=1)
        else:
            data = pd.read_csv(uploaded_file, delimiter=',|;',names=['Latitude', 'Longitude', 'TMI'],header=None, skiprows=1)
elif page == "Gravity":
    if uploaded_file is not None:
        # Read data from uploaded file
        if uploaded_file.type == "text/plain":
            data = pd.read_csv(uploaded_file, header=None, delim_whitespace=True, names=['Easting', 'Northing', 'CBA'],skiprows=1)
        else:
            data = pd.read_csv(uploaded_file, delimiter=',|;',names=['Easting', 'Northing', 'CBA'],header=None, skiprows=1)


# if uploaded_file is not None:
#     # Read data from uploaded file
#     if uploaded_file.type == "text/plain":
#         data = pd.read_csv(uploaded_file, header=None, delim_whitespace=True, names=['Easting', 'Northing', 'CBA'],skiprows=1)
#     else:
#         data = pd.read_csv(uploaded_file, delimiter=',|;',names=['Easting', 'Northing', 'CBA'],header=None, skiprows=1)
#---------------------END DATA INPUT--------------------------
xarray_grid_cba = None
height_displacement_meter = None


#----------SETTING FUNCTION-----------
st.sidebar.header("Visualization Settings")
show_interpolation_settings = st.sidebar.checkbox("Show Interpolation Settings")

# Settings for interpolation
if show_interpolation_settings:
    st.sidebar.subheader("Interpolation Settings")
    interpolation_colormap = st.sidebar.selectbox("Colormap", ["turbo", "viridis", "cividis", "gray", "plasma", "inferno", "seismic"])
    interpolation_show_contour = st.sidebar.checkbox("Show Contour")
    if interpolation_show_contour:
        interpolation_contour_levels = st.sidebar.slider("Contour Levels", min_value=1, max_value=100, value=20)
    interpolation_transparency = st.sidebar.slider("Overlay Transparency", min_value=0.0, max_value=1.0, value=0.8)

if page is not None:
    st.write(data)

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)
col5, col6 = st.columns(2)
# Display interpolation settings
if show_interpolation_settings and data is not None:
# Kriging interpolation
    if page == "Magnetic":
        easting, northing, cba = data['Latitude'].values, data['Longitude'].values, data['TMI'].values
        grid_easting, grid_northing = np.mgrid[min(easting):max(easting):1000j, min(northing):max(northing):1000j]
        grid_cba = griddata((easting, northing), cba, (grid_easting, grid_northing), method='cubic', rescale=True)
    elif page == "Gravity":
        easting, northing, cba = data['Easting'].values, data['Northing'].values, data['CBA'].values
        grid_easting, grid_northing = np.mgrid[min(easting):max(easting):1000j, min(northing):max(northing):1000j]
        grid_cba = griddata((easting, northing), cba, (grid_easting, grid_northing), method='cubic' ,rescale=True)



    # easting, northing, cba = data['Easting'].values, data['Northing'].values, data['CBA'].values
    # grid_easting, grid_northing = np.mgrid[min(easting):max(easting):1000j, min(northing):max(northing):1000j]
    # grid_cba = griddata((easting, northing), cba, (grid_easting, grid_northing), method='cubic' ,rescale=True)


    # Create a figure for plotting
    fig, ax = plt.subplots()
    cba_plot = ax.contourf(grid_northing, grid_easting, grid_cba, cmap=interpolation_colormap, levels=20, alpha=interpolation_transparency)
    if interpolation_show_contour:
        contour_plot = ax.contour(grid_northing, grid_easting, grid_cba, colors='black', levels=interpolation_contour_levels)
        ax.clabel(contour_plot, inline=True, fontsize=8, fmt='%1.1f')

    ax.axis('off')
    plt.tight_layout()
    height_displacement_meter = st.sidebar.number_input("Height Displacement (meters)", value=0.001, step=0.001)
    # Display the interpolated map
    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches='tight', pad_inches=0, transparent=True)
    plt.savefig('interpolated.png', format="png", bbox_inches='tight', pad_inches=0, transparent=True)
    buffer.seek(0)
    col1.subheader("Interpolated Map")
    col1.image(buffer)
    xarray_grid_cba = xr.DataArray(grid_cba , coords={'easting': grid_easting[:, 0], 'northing': grid_northing[0, :]}, dims=['easting', 'northing'])
    xarray_grid_cba = xarray_grid_cba.fillna(0)


#----------UPWARD CONTINUED----------
# upward_continued = hm.upward_continuation(xarray_grid_cba,
#                                           height_displacement=0.05)

show_upward_settings = st.sidebar.checkbox("Show Upward Continuation Settings")
if show_upward_settings and data is not None:
    st.sidebar.subheader("Upward Continuation Settings")
    # Settings for upward continuation
    upward_colormap = st.sidebar.selectbox("Upward Colormap", ["turbo", "viridis", "cividis", "gray", "plasma", "inferno", "seismic"])
    upward_show_contour = st.sidebar.checkbox("Show Upward Contour")
    if upward_show_contour:
        upward_contour_levels = st.sidebar.slider("Upward Contour Levels", min_value=1, max_value=100, value=20)
    upward_transparency = st.sidebar.slider("Upward Overlay Transparency", min_value=0.0, max_value=1.0, value=0.8)
    upward_continued = None

    if data is not None:
        if height_displacement_meter is not None:
            lat_meter_scale = 111000  # 1 degree latitude ≈ 111 km
            upward_continued = hm.upward_continuation(xarray_grid_cba, height_displacement=height_displacement_meter / lat_meter_scale)
    col2.subheader("Upward Continuation")

    if upward_continued is not None:
        # Create a figure for plotting
        fig_upward, ax_upward = plt.subplots()
        upward_plot = ax_upward.contourf(grid_northing, grid_easting, upward_continued, cmap=upward_colormap, levels=20, alpha=upward_transparency)
        if upward_show_contour:
            contour_upward_plot = ax_upward.contour(grid_northing, grid_easting, upward_continued, colors='black', levels=upward_contour_levels)
            ax_upward.clabel(contour_upward_plot, inline=True, fontsize=8, fmt='%1.1f')

        ax_upward.axis('off')
        plt.tight_layout()
        buffer_upward = BytesIO()
        plt.savefig(buffer_upward, format="png", bbox_inches='tight', pad_inches=0, transparent=True)
        plt.savefig('upward.png', format="png", bbox_inches='tight', pad_inches=0, transparent=True)

        buffer_upward.seek(0)

        # Display the upward continuation plot
        col2.image(buffer_upward)


# ----------DERIVATIVE----------
# deriv_northing = hm.derivative_northing(xarray_grid_cba)
# deriv_easting= hm.derivative_easting(xarray_grid_cba)

derivative_settings = st.sidebar.checkbox("Show Derivative Settings")
if  derivative_settings and data is not None:
    st.sidebar.subheader(" Derivative Settings")
    orderdev = st.sidebar.selectbox("Select Order",["1","2","3"])
    derivative_n = hm.derivative_northing(xarray_grid_cba,order=int(orderdev))
    derivative_e = hm.derivative_easting(xarray_grid_cba,order=int(orderdev))
    derivative_colormap = st.sidebar.selectbox("Derivative Colormap",
                                           ["turbo", "viridis", "cividis", "gray", "plasma", "inferno", "seismic"])
    derivative_contour = st.sidebar.checkbox("Show  Derivative Contour")
    if derivative_contour:
        derivative_contour_levels = st.sidebar.slider(" Derivative Contour Levels", min_value=1, max_value=100, value=20)
    derivative_transparency = st.sidebar.slider(" Derivative Overlay Transparency", min_value=0.0, max_value=1.0, value=0.8)

    if derivative_e is not None:
        col3.subheader("Derivative Map Easting")
        # Create a figure for plotting
        fig_derivative, ax_derivative_e = plt.subplots()
        derivative_plot = ax_derivative_e.contourf(grid_northing, grid_easting, derivative_e, cmap=derivative_colormap, levels=20, alpha=derivative_transparency)
        if derivative_contour:
            contour_derivative_plot = ax_derivative_e.contour(grid_northing, grid_easting, derivative_e, colors='black', levels=derivative_contour_levels)
            ax_derivative_e.clabel(contour_derivative_plot, inline=True, fontsize=8, fmt='%1.1f')

        ax_derivative_e.axis('off')
        plt.tight_layout()

        buffer_derivative_e = BytesIO()
        plt.savefig(buffer_derivative_e, format="png", bbox_inches='tight', pad_inches=0, transparent=True)
        plt.savefig('derivativeeast.png', format="png", bbox_inches='tight', pad_inches=0, transparent=True)
        buffer_derivative_e.seek(0)

        # Display the upward continuation plot
        col3.image(buffer_derivative_e)

    if derivative_n is not None:
        col4.subheader("Derivative Map Northing")
        # Create a figure for plotting
        fig_derivative, ax_derivative_n = plt.subplots()
        derivative_plot = ax_derivative_n.contourf(grid_northing, grid_easting, derivative_n, cmap=derivative_colormap, levels=20, alpha=derivative_transparency)
        if derivative_contour:
            contour_derivative_plot = ax_derivative_n.contour(grid_northing, grid_easting, derivative_n, colors='black', levels=derivative_contour_levels)
            ax_derivative_n.clabel(contour_derivative_plot, inline=True, fontsize=8, fmt='%1.1f')

        ax_derivative_n.axis('off')
        plt.tight_layout()

        buffer_derivative_n = BytesIO()
        plt.savefig(buffer_derivative_n,format="png", bbox_inches='tight', pad_inches=0, transparent=True)
        plt.savefig('derivativenorth.png', format="png", bbox_inches='tight', pad_inches=0, transparent=True)
        buffer_derivative_n.seek(0)

        # Display the upward continuation plot
        col4.image(buffer_derivative_n)


#----------CUTOFF WAVELENGTH----------
# cutoff_wavelength = 0.5
# magnetic_low_freqs = hm.gaussian_lowpass(xarray_grid_cba, wavelength=cutoff_wavelength)
# magnetic_high_freqs = hm.gaussian_highpass(xarray_grid_cba, wavelength=cutoff_wavelength)

cutoff_settings = st.sidebar.checkbox("Show Cutoff Wavelength Settings")
if cutoff_settings and data is not None:
    cutoff_wavelength = st.sidebar.slider("Cutoff Wavelength", min_value=0.0, max_value=5.0, value=0.5)
    st.sidebar.subheader("Cutoff Settings")
    cutlow = hm.gaussian_lowpass(xarray_grid_cba, wavelength=cutoff_wavelength)
    cuthigh = hm.gaussian_highpass(xarray_grid_cba, wavelength=cutoff_wavelength)
    cutoff_colormap = st.sidebar.selectbox("Cutoff  Colormap",["turbo", "viridis", "cividis", "gray", "plasma", "inferno", "seismic"])
    cutoff_contour = st.sidebar.checkbox("Show Cutoof Wavelength Contour")
    if cutoff_contour:
        cutoff_contour_levels = st.sidebar.slider("Cutoff Contour Levels", min_value=1, max_value=100,value=20)
    cutoff_transparency = st.sidebar.slider("Cutoff Overlay Transparency", min_value=0.0, max_value=1.0,value=0.8)

    if cutlow is not None:
        col5.subheader("Low Pass Map")
        # Create a figure for plotting
        fig_cutoff, ax_cutoffl = plt.subplots()
        cutoff_plot = ax_cutoffl.contourf(grid_northing, grid_easting, cutlow, cmap=cutoff_colormap,levels=20, alpha=cutoff_transparency)
        if cutoff_contour:
            contour_cutoff_plot = ax_cutoffl.contour(grid_northing, grid_easting, cutlow, colors='black',levels=cutoff_contour_levels)
            ax_cutoffl.clabel(contour_cutoff_plot, inline=True, fontsize=8, fmt='%1.1f')

        ax_cutoffl.axis('off')
        plt.tight_layout()
        buffer_cutoffl = BytesIO()
        plt.savefig(buffer_cutoffl, format="png", bbox_inches='tight', pad_inches=0, transparent=True)
        plt.savefig('lowpass.png', format="png", bbox_inches='tight', pad_inches=0, transparent=True)

        buffer_cutoffl.seek(0)
        col5.image(buffer_cutoffl)

    if cuthigh is not None:
        col6.subheader("High Pass Map")
        # Create a figure for plotting
        fig_cutoff, ax_cutoffh = plt.subplots()
        cutoff_plot = ax_cutoffh.contourf(grid_northing, grid_easting, cuthigh, cmap=cutoff_colormap,levels=20, alpha=cutoff_transparency)
        if cutoff_contour:
            contour_cutoff_plot = ax_cutoffh.contour(grid_northing, grid_easting, cuthigh, colors='black',levels=cutoff_contour_levels)
            ax_cutoffh.clabel(contour_cutoff_plot, inline=True, fontsize=8, fmt='%1.1f')

        ax_cutoffh.axis('off')
        plt.tight_layout()
        buffer_cutoffh = BytesIO()
        plt.savefig(buffer_cutoffh, format="png", bbox_inches='tight', pad_inches=0, transparent=True)
        plt.savefig('highpass.png', format="png", bbox_inches='tight', pad_inches=0, transparent=True)
        buffer_cutoffh.seek(0)
        col6.image(buffer_cutoffh)

        # # #----------RTP----------
        # # rtp = hm.reduction_to_pole(xarray_grid_cba, inclination = -30.5479, declination=0.619463)
        #
rtp_settings = st.sidebar.checkbox("Show RTP Settings")
if rtp_settings and data is not None:
    st.sidebar.subheader("RTP Settings")

    inclination = st.sidebar.number_input("Inclination", value=None, placeholder="Input Inclination")
    declination = st.sidebar.number_input("Declination", value=None, placeholder="Input Declination")

    if inclination is not None and declination is not None:
        rtp = hm.reduction_to_pole(xarray_grid_cba, inclination, declination)

        RTP_colormap = st.sidebar.selectbox("RTP Colormap",
                                            ["turbo", "viridis", "cividis", "gray", "plasma", "inferno", "seismic"])
        RTP_contour = st.sidebar.checkbox("Show RTP Contour")

        if RTP_contour:
            RTP_contour_levels = st.sidebar.slider("RTP Contour Levels", min_value=1, max_value=100, value=20)

        RTP_transparency = st.sidebar.slider("RTP Overlay Transparency", min_value=0.0, max_value=1.0, value=0.8)

        if rtp is not None:
            st.subheader("RTP Map")
            fig_rtp, ax_rtp = plt.subplots()
            rtp_plot = ax_rtp.contourf(grid_northing, grid_easting, rtp, cmap=RTP_colormap, levels=20,
                                       alpha=RTP_transparency)

            if RTP_contour:
                contour_rtp_plot = ax_rtp.contour(grid_northing, grid_easting, rtp, colors='black',
                                                  levels=RTP_contour_levels)
                ax_rtp.clabel(contour_rtp_plot, inline=True, fontsize=8, fmt='%1.1f')

            ax_rtp.axis('off')
            plt.tight_layout()

            buffer_RTP = BytesIO()
            plt.savefig(buffer_RTP, format="png", bbox_inches='tight', pad_inches=0, transparent=True)
            plt.savefig('rtp.png', format="png", bbox_inches='tight', pad_inches=0, transparent=True)
            buffer_RTP.seek(0)

            # Display the RTP plot
            st.image(buffer_RTP)
    else:
        print("Input Inclination and Declination")


def create_image_overlay(method, image_filename, easting, northing):

    m = folium.Map(location=[np.mean(easting), np.mean(northing)], zoom_start=15, tiles='OpenStreetMap')
    image = ImageOverlay(
        image=image_filename,
        bounds=[[min(easting), min(northing)], [max(easting), max(northing)]],
        opacity=0.8,
        name='Matplotlib Plot'
    ).add_to(m)
    m.save(f'{method.lower()}.html')

def main():
    image_filenames = {
        "Interpolation": "interpolated.png",
        "Upward": "upward.png",
        "Derivative East": "derivativeeast.png",
        "Derivative North": "derivativenorth.png",
        "High Pass": "highpass.png",
        "Low Pass": "lowpass.png",
        "RTP": "rtp.png"
    }

    option = st.sidebar.selectbox("OVERLAY", image_filenames.keys(), index=None, placeholder="Select Method")

    if option is not None:
        create_image_overlay(option, image_filenames[option], easting, northing)
        st.write('Overlay', option)
        # Display the result using Streamlit
        with open(f"{option.lower()}.html", "r", encoding="utf-8") as file:
            html_code = file.read()
        st.components.v1.html(html_code, height=600, scrolling=True)

if __name__ == "__main__":
    main()



