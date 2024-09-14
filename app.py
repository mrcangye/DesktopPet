import argparse
from typing import List, Tuple
from optimum.intel.openvino import OVModelForCausalLM
from transformers import (AutoTokenizer, AutoConfig,
                          TextIteratorStreamer, StoppingCriteriaList, StoppingCriteria)
import gradio as gr

def parse_text(text):
    lines = text.split("\n")
    lines = [line for line in lines if line != ""]
    count = 0
    for i, line in enumerate(lines):
        if "```" in line:
            count += 1
            items = line.split('`')
            if count % 2 == 1:
                lines[i] = f'<pre><code class="language-{items[-1]}">'
            else:
                lines[i] = f'<br></code></pre>'
        else:
            if i > 0:
                if count % 2 == 1:
                    line = line.replace("`", "\`")
                    line = line.replace("<", "&lt;")
                    line = line.replace(">", "&gt;")
                    line = line.replace(" ", "&nbsp;")
                    line = line.replace("*", "&ast;")
                    line = line.replace("_", "&lowbar;")
                    line = line.replace("-", "&#45;")
                    line = line.replace(".", "&#46;")
                    line = line.replace("!", "&#33;")
                    line = line.replace("(", "&#40;")
                    line = line.replace(")", "&#41;")
                    line = line.replace("$", "&#36;")
                lines[i] = "<br>" + line
    text = "".join(lines)
    return text


class StopOnTokens(StoppingCriteria):
    def __init__(self, token_ids):
        self.token_ids = token_ids

    def __call__(
            self, input_ids, scores, **kwargs
    ) -> bool:
        for stop_id in self.token_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False

LOAD_MODEL_FALG = True
if LOAD_MODEL_FALG:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-h',
                        '--help',
                        action='help',
                        help='Show this help message and exit.')
    parser.add_argument('-m',
                        '--model_path',
                        default='Source/chatglm3-6b-ov',
                        required=False,
                        type=str,
                        help='Required. model path')
    parser.add_argument('-l',
                        '--max_sequence_length',
                        default=256,
                        required=False,
                        type=int,
                        help='Required. maximun length of output')
    parser.add_argument('-d',
                        '--device',
                        default='CPU',
                        required=False,
                        type=str,
                        help='Required. device for inference, CPU with int4 needs about 10 G')
    args = parser.parse_args()
    model_dir = args.model_path

    ov_config = {"PERFORMANCE_HINT": "LATENCY",
                 "NUM_STREAMS": "1", "CACHE_DIR": ""}

    tokenizer = AutoTokenizer.from_pretrained(
        model_dir, trust_remote_code=True)

    print("====Compiling model====")
    ov_model = OVModelForCausalLM.from_pretrained(
        model_dir,
        device=args.device,
        ov_config=ov_config,
        config=AutoConfig.from_pretrained(model_dir, trust_remote_code=True),
        trust_remote_code=True,
    )

    streamer = TextIteratorStreamer(
        tokenizer, timeout=60.0, skip_prompt=True, skip_special_tokens=True
    )
    stop_tokens = [0, 2]
    stop_tokens = [StopOnTokens(stop_tokens)]

    def convert_history_to_token(history: List[Tuple[str, str]]):

        messages = []
        for idx, (user_msg, model_msg) in enumerate(history):
            if idx == len(history) - 1 and not model_msg:
                messages.append({"role": "user", "content": user_msg})
                break
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if model_msg:
                messages.append({"role": "assistant", "content": model_msg})

        model_inputs = tokenizer.apply_chat_template(messages,
                                                     add_generation_prompt=True,
                                                     tokenize=True,
                                                     return_tensors="pt")
        return model_inputs

    # history = []
    # print("====Starting conversation====")
    # while True:
    #     input_text = input("用户: ")
    #     if input_text.lower() == 'stop':
    #         break
    #
    #     if input_text.lower() == 'clear':
    #         history = []
    #         print("AI助手: 对话历史已清空")
    #         continue
    #
    #     print("ChatGLM3-6B-OpenVINO:", end=" ")
    #     history = history + [[parse_text(input_text), ""]]
    #     model_inputs = convert_history_to_token(history)
    #     generate_kwargs = dict(
    #         input_ids=model_inputs,
    #         max_new_tokens=args.max_sequence_length,
    #         temperature=0.1,
    #         do_sample=True,
    #         top_p=1.0,
    #         top_k=50,
    #         repetition_penalty=1.1,
    #         streamer=streamer,
    #         stopping_criteria=StoppingCriteriaList(stop_tokens)
    #     )
    #
    #     """
    #     t1 = Thread(target=ov_model.generate, kwargs=generate_kwargs)
    #     t1.start()
    #
    #     partial_text = ""
    #     for new_text in streamer:
    #         new_text = new_text
    #         print(new_text, end="", flush=True)
    #         partial_text += new_text
    #     print("\n")
    #     """
    #     partial_text = ov_model.generate(**generate_kwargs)
    #     # print(f"raw data is: {partial_text}")
    #     partial_text = tokenizer.decode(partial_text[0])
    #     partial_text = partial_text.split("<|assistant|> \n ")[-1]
    #     print(partial_text)
    #
    #     history[-1][1] = partial_text

def fn_send(input_text, history):
    print(input_text)
    history = history + [[parse_text(input_text), ""]]
    model_inputs = convert_history_to_token(history)
    generate_kwargs = dict(
        input_ids=model_inputs,
        max_new_tokens=args.max_sequence_length,
        temperature=0.1,
        do_sample=True,
        top_p=1.0,
        top_k=50,
        repetition_penalty=1.1,
        streamer=streamer,
        stopping_criteria=StoppingCriteriaList(stop_tokens)
    )
    partial_text = ov_model.generate(**generate_kwargs)
    # print(f"raw data is: {partial_text}")
    partial_text = tokenizer.decode(partial_text[0])
    partial_text = partial_text.split("<|assistant|> \n ")[-1]
    print(partial_text)
    history[-1][1] = partial_text
    return "", history

with gr.Blocks() as app:
    gr.Markdown("""
        # ChatGLM-6B-OpenVINO
        """)
    chatbot = gr.Chatbot(label="对话历史")
    with gr.Row():
        text_input = gr.TextArea(label="输入", placeholder="请输入", scale=5)
        btn_send = gr.Button(value="发送")
        btn_clear = gr.Button(value="清空")

    btn_send.click(fn=fn_send, inputs=[text_input, chatbot], outputs=[text_input, chatbot])
    btn_clear.click(fn=lambda: [], outputs=[chatbot])

app.launch()