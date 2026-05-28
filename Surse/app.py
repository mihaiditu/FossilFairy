import numpy as np
import pandas as pd
import gradio as gr
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import base64

available_models={
    # '🦥 Sid':'./models/sid.pkl',
    '🐯 Diego':'./models/diego.pkl',
    # '🦣 Manny':'./models/manny.pkl'
    }

artifacts = joblib.load(list(available_models.values())[0])
encoders = artifacts['encoders']

def load_model(model_name):
    global artifacts, model, encoders, minmax_scaler, standard_scaler, feature_names, fig

    artifacts = joblib.load(available_models[model_name])
    model = artifacts['model']
    encoders = artifacts['encoders']
    minmax_scaler = artifacts['minmax_scaler']
    standard_scaler = artifacts['standard_scaler']
    feature_names = artifacts['feature_names']

    fig, _ = plt.subplots()
    sns.heatmap(artifacts['confusion_matrix'], fmt='d', cmap='Blues')

    return fig


def predict_species(specimen_part, length, width, max_ma, min_ma, paleolng, paleolat, formation, lithology1, environment):
    raw_data = {
        'specimen_part': specimen_part,
        'length': length,
        'width': width,
        'max_ma': max_ma,
        'min_ma': min_ma,
        'paleolng': paleolng,
        'paleolat': paleolat,
        'formation': formation,
        'lithology1': lithology1,
        'environment': environment
    }

    input_df = pd.DataFrame([raw_data])[feature_names]

    string_fields = ['specimen_part', 'formation', 'lithology1', 'environment']
    for col in string_fields:
        input_df[col] = encoders[col].transform(input_df[col])

    scaled_fields = ['length', 'width', 'max_ma', 'min_ma', 'paleolng', 'paleolat']
    input_df[scaled_fields] = minmax_scaler.transform(input_df[scaled_fields])
    input_df[scaled_fields] = standard_scaler.transform(input_df[scaled_fields])

    probabilities = model.predict_proba(input_df)[0]
    species_indexes = model.classes_

    predicted_species = encoders['accepted_name'].inverse_transform(species_indexes)
    confidences = {predicted_species[i]: float(probabilities[i]) for i in range(len(predicted_species))}

    return confidences

with open("fossil_fairy.png", "rb") as fossil_fairy_image:
    encoded_image_string = base64.b64encode(fossil_fairy_image.read()).decode()
html_image = f"<img src='data:image/png;base64,{encoded_image_string}' width='64' style='display: inline-block;'>"

with gr.Blocks() as demo:
    gr.Markdown(f"# {html_image} Fossil Fairy")

    with gr.Row(equal_height=True):
        with gr.Column():
            specimen_part = gr.Dropdown(label="Specimen Part", choices=list(encoders['specimen_part'].classes_), value='m1')
            length = gr.Number(label="Length (mm)", value=2.7)
            width = gr.Number(label="Width (mm)", value=2.5)
            max_ma = gr.Slider(label="Max Ma (millions of years ago)", minimum=0, maximum=200, step=0.1, value=60.9)
            min_ma = gr.Slider(label="Min Ma (millions of years ago)", minimum=0, maximum=200, step=0.1, value=57.5)

        with gr.Column():
            paleolng = gr.Slider(label="Paleolongitude", minimum=-180, maximum=180, step=0.01, value=-75.50)
            paleolat = gr.Slider(label="Paleolatitude", minimum=-90, maximum=90, step=0.01, value=53.44)
            formation = gr.Dropdown(label="Formation", choices=list(encoders['formation'].classes_), value='Fort Union')
            lithology1 = gr.Dropdown(label="Lithology", choices=list(encoders['lithology1'].classes_), value='siliciclastic')
            environment = gr.Dropdown(label="Environment", choices=list(encoders['environment'].classes_), value='fluvial-lacustrine indet.')

    with gr.Row(equal_height=True):
        with gr.Column():
            chosen_model = gr.Dropdown(label='Model', choices=list(available_models.keys()), value=list(available_models.keys())[0])

        with gr.Column(scale=2):
            submit_btn = gr.Button("PREDICT", variant="primary")

    with gr.Row(equal_height=True):
        with gr.Column():
            matrix_plot = gr.Plot(label=f"Confusion Matrix for the selected model")

        with gr.Column(scale=2):
            output_confidences = gr.Label(label="Predicted Species", num_top_classes=5)

    submit_btn.click(
        fn=predict_species,
        inputs=[specimen_part, length, width, max_ma, min_ma, paleolng, paleolat, formation, lithology1, environment],
        outputs=output_confidences
    )

    chosen_model.change(
        fn=load_model,
        inputs=chosen_model,
        outputs=matrix_plot
    )

    gr.Markdown("Project by **Mihai-Nicolae Dițu** & **Robert-Adrian Rizoiu**")

    demo.load(
        fn=load_model,
        inputs=chosen_model,
        outputs=matrix_plot
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Ocean())