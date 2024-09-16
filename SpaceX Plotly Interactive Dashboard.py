import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# Read the SpaceX data into a pandas DataFrame
spacex_df = pd.read_csv("spacex_launch_dash.csv")
spacex_df['class'] = pd.to_numeric(spacex_df['class'], errors='coerce')
spacex_df = spacex_df.dropna(subset=['class'])
spacex_df['class'] = spacex_df['class'].astype(int)

max_payload = spacex_df['Payload Mass (kg)'].max()
min_payload = spacex_df['Payload Mass (kg)'].min()

# Create a Dash application
app = dash.Dash(__name__)

# Create an app layout
app.layout = html.Div(children=[
    html.H1('SpaceX Launch Records Dashboard',
            style={'textAlign': 'center', 'color': '#503D36', 'font-size': 40}),
    
    dcc.Dropdown(
        id='site-dropdown',
        options=[
            {'label': 'All Sites', 'value': 'ALL'},
            {'label': 'CCAFS LC-40', 'value': 'CCAFS LC-40'},
            {'label': 'VAFB SLC-4E', 'value': 'VAFB SLC-4E'},
            {'label': 'KSC LC-39A', 'value': 'KSC LC-39A'},
            {'label': 'CCAFS SLC-40', 'value': 'CCAFS SLC-40'},
        ],
        value='ALL',
        placeholder="Select a Launch Site here",
        searchable=True
    ),
    html.Br(),

    html.Div(dcc.Graph(id='success-pie-chart')),
    html.Br(),

    html.P("Payload range (Kg):"),
    dcc.RangeSlider(
        id='payload-slider',
        min=0, max=10000, step=1000,
        marks={i: str(i) for i in range(0, 10001, 1000)},
        value=[min_payload, max_payload]
    ),

    html.Div(dcc.Graph(id='success-payload-scatter-chart')),
])

# Primary color palette
primary_colors = ['#FF0000', '#0000FF', '#FFFF00', '#00FF00', '#FFA500', '#800080', '#008080']

@app.callback(
    Output(component_id='success-pie-chart', component_property='figure'),
    Input(component_id='site-dropdown', component_property='value')
)
def get_pie_chart(entered_site):
    if entered_site == 'ALL':
        success_df = spacex_df[spacex_df['class'] == 1].groupby('Launch Site').size().reset_index(name='count')
        fig = px.pie(success_df, 
                     values='count', 
                     names='Launch Site',
                     title='Total Successful Launches by Site',
                     color_discrete_sequence=primary_colors)
    else:
        site_df = spacex_df[spacex_df['Launch Site'] == entered_site]
        fig = px.pie(site_df, 
                     names='class',
                     title=f'Launch Outcomes for {entered_site}',
                     color_discrete_sequence=[primary_colors[0], primary_colors[1]],  # Red for failure, Blue for success
                     labels={0: 'Failure', 1: 'Success'})
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig

@app.callback(
    Output('success-payload-scatter-chart', 'figure'),
    [Input('site-dropdown', 'value'),
     Input('payload-slider', 'value')]
)
def update_scatter_plot(selected_site, payload_range):
    try:
        min_payload, max_payload = payload_range
        filtered_df = spacex_df[(spacex_df['Payload Mass (kg)'] >= min_payload) &
                                (spacex_df['Payload Mass (kg)'] <= max_payload)]

        if selected_site == 'ALL':
            fig = px.scatter(
                filtered_df,
                x='Payload Mass (kg)',
                y='class',
                color='Booster Version Category',
                title='Payload Mass vs. Success for All Sites',
                labels={'class': 'Launch Outcome'},
                category_orders={'class': [0, 1]},
                hover_data=['Launch Site'],
                color_discrete_sequence=primary_colors
            )
        else:
            filtered_df = filtered_df[filtered_df['Launch Site'] == selected_site]
            fig = px.scatter(
                filtered_df,
                x='Payload Mass (kg)',
                y='class',
                color='Booster Version Category',
                title=f'Payload Mass vs. Success for {selected_site}',
                labels={'class': 'Launch Outcome'},
                category_orders={'class': [0, 1]},
                hover_data=['Launch Site'],
                color_discrete_sequence=primary_colors
            )

        fig.update_yaxes(tickvals=[0, 1], ticktext=['Failure', 'Success'])
        
        # Enhance the scatter plot appearance
        fig.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey')),
                          selector=dict(mode='markers'))
        fig.update_layout(
            plot_bgcolor='rgba(240,240,240,0.5)',  # Light gray background
            paper_bgcolor='white',
            font=dict(color='#333')  # Dark gray font for better readability
        )
        
        return fig
    except Exception as e:
        print(f"Error in update_scatter_plot: {str(e)}")
        return px.scatter(title="Error: Unable to load scatter plot")

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)