from transformers import AutoTokenizer, BartForConditionalGeneration

MODEL = "facebook/bart-large-cnn"
model = BartForConditionalGeneration.from_pretrained(MODEL)
tokenizer = AutoTokenizer.from_pretrained(MODEL)

def summarize_text_with_my_model(text):
    print(f"\nSummarizing text using {MODEL} model...")
    inputs = tokenizer([(text)], max_length=1024, return_tensors="pt")

    # Generate Summary
    summary_ids = model.generate(inputs["input_ids"], num_beams=2, min_length=0)
    summary = tokenizer.batch_decode(summary_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
    print(f"\nReturning summary from {MODEL} model:")
    print(summary)
    print("\n")
    return summary