import os
import gradio as gr
from invoker import ExpertAssistant
from utils.ui_settings import UISettings

# Initialize the ExpertAssistant
expert = ExpertAssistant()

def process_uploaded_files(files, chatbot, app_functionality):
    if app_functionality == "Reporte de propiedad":
        for file in files:
            expert.process_file(file.name)
        chatbot.append(("File(s) processed successfully!", None))
    return "", chatbot

def respond_to_query(chatbot, input_txt, chat_type, app_functionality):
    if app_functionality == "Chat":
        response = expert.process_user_query(input_txt)
        chatbot.append((input_txt, response))
    elif app_functionality == "Reporte de propiedad":
        response = expert.analyze_url(chat_type)  # Assuming expert has a method to analyze URL
        chatbot.append((chat_type, response))
    return "", chatbot

with gr.Blocks(css=".gradio-container {background-color: #ff3131}") as demo:
    with gr.Tabs():
        with gr.TabItem("Hola! Soy Brick, tu agente experto en emprendimientos de pozo. ¿En qué puedo ayudarte?"):
            with gr.Row():
                with gr.Column(scale=6):
                    chatbot = gr.Chatbot(
                        [],
                        elem_id="chatbot",
                        bubble_full_width=False,
                        height=500,
                        avatar_images=(
                            ("assets/brickland_icon.png"), "images/openai.png")
                    )
                    # **Adding like/dislike icons
                    chatbot.like(UISettings.feedback, None, None)

                    input_txt = gr.Textbox(
                        lines=4,
                        scale=8,
                        placeholder="Escribí acá tu pregunta",
                        container=False,
                    )

                    with gr.Row():
                        url_box = gr.Textbox(
                            label="Insertar URL",
                            placeholder="Insertar URL para analizar"
                        )
                        app_functionality = gr.Dropdown(
                            label="Modalidad de Chat", choices=["Chat", "Reporte de propiedad"], value="Chat")

                    with gr.Row():
                        text_submit_btn = gr.Button(value="Preguntar!")
                        clear_button = gr.ClearButton(value="Borrar",inputs=[input_txt, chatbot])
                        create_report_btn = gr.Button("Crear reporte")

            with gr.Row():
                file_msg = create_report_btn.click(fn=process_uploaded_files, inputs=[
                    create_report_btn, chatbot, app_functionality], outputs=[input_txt, chatbot], queue=False)

                txt_msg = input_txt.submit(fn=respond_to_query,
                                           inputs=[chatbot, input_txt,
                                                   url_box, app_functionality],
                                           outputs=[input_txt,
                                                    chatbot],
                                           queue=False).then(lambda: gr.Textbox(interactive=True),
                                                             None, [input_txt], queue=False)

                txt_msg = text_submit_btn.click(fn=respond_to_query,
                                                inputs=[chatbot, input_txt,
                                                        url_box, app_functionality],
                                                outputs=[input_txt,
                                                         chatbot],
                                                queue=False).then(lambda: gr.Textbox(interactive=True),
                                                                  None, [input_txt], queue=False)

if __name__ == "__main__":
    demo.launch()
