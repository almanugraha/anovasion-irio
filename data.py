import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pyreadr as pr
import requests

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from yellowbrick.cluster import KElbowVisualizer
from src.agstyler import *


## LOAD DATA
df_pdrb = pr.read_r("data/rds/data_pdrb.rds")[None]
df_eksim = pr.read_r('data/rds/data_eksim_ap.rds')[None]
df_flbl = pr.read_r('data/rds/flbl_detail.rds')[None]
leontif = pr.read_r("data/rds/leontif.rds")[None]
base_irio = pr.read_r("data/rds/sim_irio.rds")[None]
out_irio = pr.read_r("data/rds/out_irio.rds")[None]

X_FD2 = pd.read_csv('data/csv/X_FD.csv', sep=';')
X_F2 = pd.read_csv('data/csv/X_F.csv', sep=';')
X_B2 = pd.read_csv('data/csv/X_B.csv', sep=';')
X_P12 = pd.read_csv('data/csv/X_P1.csv', sep=';')
X_P22 = pd.read_csv('data/csv/X_P2.csv', sep=';')
X_P32 = pd.read_csv('data/csv/X_P3.csv', sep=';')
X_E12 = pd.read_csv('data/csv/X_E1.csv', sep=';')
X_E22 = pd.read_csv('data/csv/X_E2.csv', sep=';')

## TAB PDRB
df_pdrb_nasional = df_pdrb.groupby(['jenis_pdrb', 'nama_komp']).agg({"nilai_jt": "sum"}).reset_index()
opt_provinsi = df_pdrb['nama_prov'].unique()
opt_sektor_prod = df_pdrb.loc[df_pdrb['jenis_pdrb'].isin(['PRODUKSI'])]['nama_komp'].unique()
opt_sektor_peng = df_pdrb.loc[df_pdrb['jenis_pdrb'].isin(['PENGELUARAN'])]['nama_komp'].unique()
opt_sektor_pend = df_pdrb.loc[df_pdrb['jenis_pdrb'].isin(['PENDAPATAN'])]['nama_komp'].unique()

def plotBerdasarkanJenisPDRB(jenis_pdrb, nama_prov, nama_sektor):
    data = df_pdrb[df_pdrb['jenis_pdrb'] == jenis_pdrb][df_pdrb['nama_prov'].isin(nama_prov)][df_pdrb['nama_komp'].isin(nama_sektor)]
    x = data['nama_prov'].unique()
    fig = go.Figure()
    komps = data['nama_komp'].unique()
    for i in range(len(komps)):
        fig.add_trace(go.Bar(x=x, y=data['nilai_jt'][data['nama_komp'] == komps[i]], name=komps[i]))
    fig.update_layout(barmode='stack')
    return(data, fig)

def plotNasionalBerdasarkanJenisPDRB(jenis_pdrb, nama_sektor, n):
    data = df_pdrb_nasional[df_pdrb_nasional['jenis_pdrb'] == jenis_pdrb][df_pdrb_nasional['nama_komp'].isin(nama_sektor)].sort_values(['nilai_jt'], ascending=False)
    data2 = data.head(n).sort_values(['nilai_jt'], ascending=True)
    x = data2['nama_komp'].unique()
    fig = go.Figure(go.Bar(
            x=data2['nilai_jt'],
            y=x,
            orientation='h'))
    fig.update_layout(barmode='stack')
    return(data, fig)

## SPATIAL
geojson = requests.get(
    "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/indonesia.geojson"
).json()

d_find_and_replace = {'Bangka-Belitung' : 'Kep. Bangka Belitung', 
                      'Kepulauan Riau' : 'Kep. Riau', 
                      'Jakarta Raya' : 'DKI Jakarta',
                      'Yogyakarta' : 'DI Yogyakarta'}

for i in range(0, 34):
    for bef in d_find_and_replace.keys():
        if geojson['features'][i]['properties']['state'] == bef:
            geojson['features'][i]['properties']['state'] = d_find_and_replace[bef]

df = pd.DataFrame(
    {"Column": pd.json_normalize(geojson["features"])["properties.state"]}
).assign(Columnnext=lambda d: d["Column"].str.len())

def plotSpatial(dat):
    df2 = df.merge(dat, left_on='Column', right_on='kode_prov')
    fig = go.Figure(
        data=go.Choropleth(
            geojson=geojson,
            locations=df["Column"], 
            featureidkey="properties.state",
            z=df2['nilai_mil'],
            colorscale="Reds",
            colorbar_title="Column"))
    fig.update_layout(autosize=True,
                        margin = dict(
                                l=0,
                                r=0,
                                b=0,
                                t=0,
                                pad=4,
                                autoexpand=True
                            ),
                            width = 1200
                            )
    fig.update_geos(fitbounds="locations", visible=False)
    return(fig)

## TAB EKSIM
opt_eksim_ind = df_eksim['nama_ind_eks'].unique()

def filterTableEksim(crit, crit2, jenis):
    if crit == 'Provinsi':
        if jenis == 'Ekspor antar Provinsi':
            data = df_eksim[df_eksim['nama_prov_eks'] == crit2]
        elif jenis == 'Impor antar Provinsi':
            data = df_eksim[df_eksim['nama_prov_imp'] == crit2]
        else :
            data = (df_eksim[df_eksim['nama_prov_eks'] == crit2]
                    .sort_values(by=['kode_prov_eks', 'nama_prov_eks', 
                           'kode_prov_imp', 'nama_prov_imp',
                           'kode_ind_eks', 'nama_ind_eks',
                           'penggunaan']))
            data_imp = (df_eksim[df_eksim['nama_prov_imp'] == crit2]
                        .sort_values(by=['kode_prov_imp', 'nama_prov_imp', 
                             'kode_prov_eks', 'nama_prov_eks',
                             'kode_ind_eks', 'nama_ind_eks',
                             'penggunaan']))
            data['nilai_mil'] = data['nilai_mil'].values - data['nilai_mil'].values
    else:
        data = df_eksim[df_eksim['nama_ind_eks'] == crit2]
    return data
            
def makeTableEksImp(crit, crit2, jenis):
    if crit == 'Provinsi':
        if jenis == 'Ekspor antar Provinsi':
        # PROV - Ekspor antar Provinsi
            df = (df_eksim[df_eksim['nama_prov_eks'] == crit2]
                .groupby('nama_prov_imp', as_index=False)
                .agg(nilai_mil=('nilai_mil', 'sum'))
                .assign(kode_prov=lambda x: x['nama_prov_imp']))
        # PROV - Impor antar Provinsi
        elif jenis == 'Impor antar Provinsi':
            df = (df_eksim[df_eksim['nama_prov_imp'] == crit2]
                .groupby('nama_prov_eks', as_index=False)
                .agg(nilai_mil=('nilai_mil', 'sum'))
                .assign(kode_prov=lambda x: x['nama_prov_eks']))
        # PROV - Net Ekspor
        else:
            df = (df_eksim[df_eksim['nama_prov_eks'] == crit2]
                .groupby('nama_prov_imp', as_index=False)
                .agg(nilai_mil=('nilai_mil', 'sum'))
                .assign(kode_prov=lambda x: x['nama_prov_imp']))
            df_im = (df_eksim[df_eksim['nama_prov_imp'] == crit2]
                .groupby('nama_prov_eks', as_index=False)
                .agg(nilai_mil=('nilai_mil', 'sum'))
                .assign(kode_prov=lambda x: x['nama_prov_eks']))
            df['nilai_mil'] = df['nilai_mil'] - df_im['nilai_mil']
    else:
        if jenis == "Ekspor antar Provinsi":
            df = (df_eksim[df_eksim['nama_ind_eks'] == crit2]
                .groupby('nama_prov_eks', as_index=False)
                .agg(nilai_mil=('nilai_mil', 'sum'))
                .assign(kode_prov=lambda x: x['nama_prov_eks']))
        elif jenis == "Impor antar Provinsi":
            df = (df_eksim[df_eksim['nama_ind_eks'] == crit2]
                .groupby('nama_prov_imp', as_index=False)
                .agg(nilai_mil=('nilai_mil', 'sum'))
                .assign(kode_prov=lambda x: x['nama_prov_imp']))
        else:
            df = (df_eksim[df_eksim['nama_ind_eks'] == crit2]
                .groupby('nama_prov_eks', as_index=False)
                .agg(nilai_mil=('nilai_mil', 'sum'))
                .assign(kode_prov=lambda x: x['nama_prov_eks']))
            df_im = (df_eksim[df_eksim['nama_ind_eks'] == crit2]
                    .groupby('nama_prov_imp', as_index=False)
                    .agg(nilai_mil=('nilai_mil', 'sum'))
                    .assign(kode_prov=lambda x: x['nama_prov_imp']))
            df['nilai_mil'] = df['nilai_mil'] - df_im['nilai_mil']
    return df

def get_total_eksim(crit, crit2, data_eksim):
    if crit == "Provinsi":
        tot_eks = (data_eksim[data_eksim['nama_prov_eks'] == crit2]
                   .agg(nilai_mil=('nilai_mil', 'sum')))
        
        tot_imp = (data_eksim[data_eksim['nama_prov_imp'] == crit2]
                   .agg(nilai_mil=('nilai_mil', 'sum')))
    else:
        tot_eks = (data_eksim[data_eksim['nama_ind_eks'] == crit2]
                   .agg(nilai_mil=('nilai_mil', 'sum')))
        
        tot_imp = tot_eks
    
    return tot_eks['nilai_mil'], tot_imp['nilai_mil']

def makeBarChart(df, colx, coly):
    fig = px.bar(df, x=colx, y=coly, color=colx, height=400)
    return fig

def plotSankey(df, crit1, crit2):
    if crit1 == 'Provinsi':
        inp = 'nama_prov_eks'
        out = 'nama_prov_imp'
    else:
        inp = 'nama_ind_eks'
        out = 'penggunaan'
    
    df['color'] = ''
    temp = list(df[inp].unique()) + list(df[out].unique())    
    for i in range(len(temp)):
        for j in range(len(df)):
            if temp[i] == df.loc[j, inp]:
                df.loc[j, inp] = i
                df.loc[j, 'color'] = 'rgba({}, {}, 20, 0.7)'.format(j*10, i*30)
            if temp[i] == df.loc[j, out]:
                df.loc[j, out] = i
                
    fig = go.Figure(data=[go.Sankey(
            node = dict(
            pad = 15,
            thickness = 20,
            line = dict(color = "black", width = 0.5),
            label = temp,
            color = "black"
            ),
            link = dict(
            source = df[df[inp] == temp.index(crit2)][inp], 
            target = df[out],
            value = df['total'],
            color = df['color']
    ))])
    fig.update_layout(title_text="Sankey Diagram dari Alur Ekspor-Impor dari {} {} (Miliar Rupiah)".format(crit1, crit2), font_size=10, height = 750)
    return(fig)

def plotSunburst(df, crit1, crit2):
    if crit1 == 'Provinsi':
        df2 = df[df['nama_prov_eks'] == crit2]
        p1, p2 = 'nama_prov_imp', 'nama_ind_eks'
    else:
        df2 = df[df['nama_ind_eks'] == crit2]
        p1, p2 = 'nama_prov_eks', 'nama_prov_imp'
    fig = px.sunburst(
        df2,
        path=[p1, p2],
        values='nilai_mil',
        title="Sunburst Diagram dari Alur Ekspor-Impor {} {} (Miliar Rupiah)".format(crit1, crit2))
    fig.update_traces(textinfo="label+percent parent")
    fig.update_layout(height = 700)
    return(fig)

def plotTreeMap(df, crit):
    if crit == 'Provinsi':
        inp1 = 'nama_prov_eks'
        inp2 = 'nama_ind_eks'
    else :
        inp1 = 'penggunaan'
        inp2 = 'nama_prov_eks'
    fig = px.treemap(df,
        path=[inp1, inp2],
        values='nilai_mil',
        title="Tree Map Diagram dari Alur Ekspor-Impor berdasarkan {} (Miliar Rupiah)".format(crit)
    )
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    return(fig)

## TAB FL-BL

def makeScatterPlotFLBL(df, prov):
    data = df[df['nama_prov'] == prov]
    fig = px.scatter(data, x='n_forward', y='n_backward',
                 title='Grafik Forward-Backward Linkage Provinsi {}'.format(prov),
                 labels={'n_forward': 'Forward', 'n_backward': 'Backward'},
                 template='simple_white', custom_data=['nama_ind'])
    fig.update_traces(marker=dict(size=13,
                                color='LightSkyBlue',
                                line=dict(width=2,
                                            color='DarkSlateGrey')),
                    hovertemplate="<br>".join([
                        "Forward: %{x}",
                        "Backward: %{y}",
                        "%{customdata[0]}"]))
    fig.add_hline(y=1, line_width=2, opacity=0.8)
    fig.add_vline(x=1, line_width=2, opacity=0.8)
    fig.update_layout(yaxis=dict(showline=False),
                    xaxis=dict(showline=False))
    return(data, fig)

## TAB CLUSTERING

def concatTables(*dfs):
    df = pd.concat(dfs, axis=1)
    return(df)

def gabung_string(group):
    return ', '.join(group)

def clusterProvince(df):
    prov = X_FD2['provinsi']
    if 'provinsi' in df.columns:
        df.drop('provinsi', axis=1, inplace=True)
    ms = StandardScaler()
    X = pd.DataFrame(ms.fit_transform(df), columns=[df.columns])
    model = KMeans()
    visualizer = KElbowVisualizer(model, k=(2,30), timings= True)
    visualizer.fit(X)
    k = visualizer.elbow_value_
    if k > 5: k=5
    kmeans = KMeans(n_clusters=k, random_state=5)
    kmeans.fit(X)
    df['Segment'] = kmeans.labels_ + 1
    labels = kmeans.labels_
    centroids = kmeans.cluster_centers_
    df_segm_analysis = df.groupby(['Segment']).mean()
    df_segm_analysis['N Obs'] = df.groupby(['Segment']).size()
    df_segm_analysis['Prop Obs'] = df_segm_analysis['N Obs'] / df_segm_analysis['N Obs'].sum()
    hasil2 = pd.concat([prov, pd.DataFrame({'Segment': labels + 1})], axis=1)
    df_segm_analysis['Provinsi'] = hasil2.groupby('Segment')['provinsi'].apply(gabung_string)
    centroid =  pd.DataFrame(centroids)
    return(hasil2, df_segm_analysis, centroid)

def plotSpatial2(dat):
    df2 = df.merge(dat, left_on='Column', right_on='provinsi')
    colors = ['#449A04', '#73C50B', '#0D5FDD', '#DD3B7A', '#AD2054']
    cc_scale = (
        [(0, colors[0])]
        + [(0.25, colors[1])] + [(0.5, colors[2])]+ [(0.75, colors[3])]
        + [(1, colors[4])])
    fig = go.Figure(
        data=go.Choropleth(
            geojson=geojson,
            locations=df["Column"], 
            featureidkey="properties.state",
            z=df2['Segment'],
            coloraxis="coloraxis")).update_layout(coloraxis={"colorscale": cc_scale})
    fig.update_layout(autosize=True,
                        margin = dict(
                                l=0,
                                r=0,
                                b=0,
                                t=0,
                                pad=4,
                                autoexpand=True
                            ),
                            width = 1200
                            )
    fig.update_geos(fitbounds="locations", visible=False)
    return(fig)

## SIMULASI
opt_ind = base_irio['nama_ind'].unique()

def simulationIRIO(df):
    fd_sim = (df['target']/100+1) * df['final_demand']
    out_sim = np.matmul(np.array(leontif.iloc[:, 1:]), np.array(fd_sim))
    pdrb_sim = out_sim * out_irio['prdb_prop']
    tot_awal = (df['nilai_jt'].sum()/1000000).round(3)
    tot_akhir = (pdrb_sim.sum()/1000000).round(3)
    return(tot_awal, tot_akhir)