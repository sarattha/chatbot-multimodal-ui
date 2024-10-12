import gradio as gr
import time
from openai import AzureOpenAI
import base64
from mimetypes import guess_type


# Set up
api_base = "<your_azure_openai_endpoint>"  # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
api_key = "<your_azure_openai_key>"
deployment_name = "<your_deployment_name>"
api_version = "2024-02-15-preview"  # this might change in the future

client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    base_url=f"{api_base}openai/deployments/{deployment_name}",
)


# Function to encode a local image into data URL
def local_image_to_data_url(image_path):
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = "application/octet-stream"  # Default MIME type if none is found

    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Construct the data URL
    return f"data:{mime_type};base64,{base64_encoded_data}"


# Chatbot demo with multimodal input (text, markdown, LaTeX, code blocks, image, audio, & video). Plus shows support for streaming text.


def print_like_dislike(x: gr.LikeData):
    print(x.index, x.value, x.liked)


def add_message(history, message):
    for x in message["files"]:
        print(f"[INFO] Uploaded image path: {x}")

        # Example usage of parsing image to GPT
        data_url = local_image_to_data_url(x)
        print("[INFO] Data URL:", data_url[:40])
        # Pass to gpt in the form below
        # When your base64 image data is ready, you can pass it to the API in the request body like this:
        # response = client.chat.completions.create(
        #     model=deployment_name,
        #     messages=[
        #         { "role": "system", "content": "You are a helpful assistant." },
        #         { "role": "user", "content": [
        #             {
        #                 "type": "text",
        #                 "text": "Describe this picture:"
        #             },
        #             {
        #                 "type": "image_url",
        #                 "image_url": {
        #                     "url": "<image URL>"
        #                 }
        #             }
        #         ] }
        #     ],
        #     max_tokens=2000
        # )

        # ...
        # "type": "image_url",
        # "image_url": {
        # "url": "data:image/jpeg;base64,<your_image_data>"
        # }
        # ...
        history.append({"role": "user", "content": {"path": x}})
    if message["text"] is not None:
        history.append({"role": "user", "content": message["text"]})
    return history, gr.MultimodalTextbox(value=None, interactive=False)


def bot(history: list):
    response = "**That's cool!**"

    # When GPT return result, it will be in the body below
    #     {
    #     "id": "chatcmpl-8VAVx58veW9RCm5K1ttmxU6Cm4XDX",
    #     "object": "chat.completion",
    #     "created": 1702439277,
    #     "model": "gpt-4",
    #     "prompt_filter_results": [
    #         {
    #             "prompt_index": 0,
    #             "content_filter_results": {
    #                 "hate": {
    #                     "filtered": false,
    #                     "severity": "safe"
    #                 },
    #                 "self_harm": {
    #                     "filtered": false,
    #                     "severity": "safe"
    #                 },
    #                 "sexual": {
    #                     "filtered": false,
    #                     "severity": "safe"
    #                 },
    #                 "violence": {
    #                     "filtered": false,
    #                     "severity": "safe"
    #                 }
    #             }
    #         }
    #     ],
    #     "choices": [
    #         {
    #             "finish_reason":"stop",
    #             "index": 0,
    #             "message": {
    #                 "role": "assistant",
    #                 "content": "The picture shows an individual dressed in formal attire, which includes a black tuxedo with a black bow tie. There is an American flag on the left lapel of the individual's jacket. The background is predominantly blue with white text that reads \"THE KENNEDY PROFILE IN COURAGE AWARD\" and there are also visible elements of the flag of the United States placed behind the individual."
    #             },
    #             "content_filter_results": {
    #                 "hate": {
    #                     "filtered": false,
    #                     "severity": "safe"
    #                 },
    #                 "self_harm": {
    #                     "filtered": false,
    #                     "severity": "safe"
    #                 },
    #                 "sexual": {
    #                     "filtered": false,
    #                     "severity": "safe"
    #                 },
    #                 "violence": {
    #                     "filtered": false,
    #                     "severity": "safe"
    #                 }
    #             }
    #         }
    #     ],
    #     "usage": {
    #         "prompt_tokens": 1156,
    #         "completion_tokens": 80,
    #         "total_tokens": 1236
    #     }
    # }
    ##
    history.append({"role": "assistant", "content": ""})
    for character in response:
        history[-1]["content"] += character
        time.sleep(0.05)
        yield history


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(elem_id="chatbot", bubble_full_width=False, type="messages")

    chat_input = gr.MultimodalTextbox(
        interactive=True,
        file_count="multiple",
        placeholder="Enter message or upload file...",
        show_label=False,
    )

    chat_msg = chat_input.submit(
        add_message, [chatbot, chat_input], [chatbot, chat_input]
    )
    bot_msg = chat_msg.then(bot, chatbot, chatbot, api_name="bot_response")
    bot_msg.then(lambda: gr.MultimodalTextbox(interactive=True), None, [chat_input])

    chatbot.like(print_like_dislike, None, None, like_user_message=True)

demo.launch()
