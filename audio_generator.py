import asyncio
import edge_tts

# Define a short script with two different voices
speakers = [
    {"name": "Manager", "voice": "en-US-GuyNeural", "text": "Good morning everyone. Let's get settled. Today is January 20th, 2026. We are exactly one week out from our hard deadline on January 27th. This MoM AI project is the priority. We need to walk through the entire pipeline, from the moment a user hits the 'Generate' button on our new UI until the final JSON is returned by Ollama. Sonia, let's start with the backend stability."},
    {"name": "Sonia", "voice": "en-GB-SoniaNeural", "text": "Thanks. On the backend, I've spent the last 48 hours refining the main.py and whisper_gpu files. The core issue we had last week was the CUDA Out-of-Memory error when switching from transcription to extraction. To fix this, I've formalized the release_gpu function. It now explicitly calls torch.cuda.empty_cache() and deletes the model variable from memory before we even initiate the request to Ollama. This is critical because Llama 3.1 8B requires about 5.5 gigabytes of VRAM in the quantized format we are using, and Whisper takes about 2 to 3 gigabytes. On an 8 gigabyte card, we were redlining."},
    {"name": "Natasha", "voice": "en-AU-NatashaNeural", "text": "I've been monitoring those VRAM spikes during my stress tests. Sonia, the cache clearing is definitely working better, but I've noticed a 3-second hang-time during the handover. Is that something we can optimize, or is that just the hardware latency for the GPU to reallocate memory blocks?"},
    {"name": "Sonia", "voice": "en-GB-SoniaNeural", "text": "It's mostly hardware latency, Natasha. Moving the weights out of the GPU and loading the next model takes time. For the MVP, I think 3 seconds is acceptable as long as the UI shows a 'loading' state so the user doesn't think the app crashed."},
    {"name": "Manager", "voice": "en-US-GuyNeural", "text": "Speaking of the UI, Prabhat, where do we stand on the frontend? We need it to be clean and modern for the client demo on Friday."},
    {"name": "Prabhat", "voice": "en-IN-PrabhatNeural", "text": "The UI is mostly ready. I’ve implemented the Tailwind CSS layout we discussed. I also added the logic where the upload box changes color and displays the filename once a file is selected. Users were getting confused before, but now they get immediate feedback. One thing I'm still working on is the concurrency issue. If multiple people hit the server at once, the GPU will crash because we don't have a queue yet. I'm going to set up a Redis queue. I'll have a prototype by Wednesday, but for the January 27th launch, we might have to stick to a single-processing stream to ensure stability."},
    {"name": "Natasha", "voice": "en-AU-NatashaNeural", "text": "Prabhat, if we limit it to a single stream, we need to make sure the UI tells the user 'Server Busy' rather than just letting the request time out. Otherwise, our QA scores will tank."},
    {"name": "Prabhat", "voice": "en-IN-PrabhatNeural", "text": "Good point. I'll add a status check that queries the backend to see if the GPU is currently locked before allowing a new upload."},
    {"name": "Manager", "voice": "en-US-GuyNeural", "text": "Let's talk models. Roger, you’ve been testing the output quality. Are we 100% sure about Llama 3.1 8B?"},
    {"name": "Roger", "voice": "en-US-RogerNeural", "text": "Yes. We tested the 70B model, but even with high quantization, the inference time per meeting was over 4 minutes. The 8B-instruct-q4_K_M version in Ollama is giving us near-instant extraction once the transcript is ready. The accuracy on identifying action items is around 94%, which is higher than the client's requirement of 90%. I’m also using Edge TTS to generate synthetic noise-heavy meetings to simulate real-world office environments. Natasha, I'll send you those noisy audio files by Thursday afternoon so you can run the final stress tests."},
    {"name": "Sonia", "voice": "en-GB-SoniaNeural", "text": "I can also add a 'Download PDF' button to the results page. I'll use a simple client-side library to convert the JSON data into a formatted document. I should have that implemented by Friday morning."},
    {"name": "Manager", "voice": "en-US-GuyNeural", "text": "Okay, let's recap the tasks and deadlines. Prabhat, you are finalizing the Redis queue and the 'Server Busy' UI state by Wednesday. Sonia, you're adding the PDF export by Friday. Roger, you're delivering the noise-test audio files to Natasha by Thursday. Natasha, your final QA sign-off is due by the end of the day Thursday. If everything looks good, we go live on January 27th. Any questions?"},
    {"name": "Prabhat", "voice": "en-IN-PrabhatNeural", "text": "Just one. Are we supporting mobile uploads for the MVP?"},
    {"name": "Manager", "voice": "en-US-GuyNeural", "text": "Not for this version. Stick to the desktop web interface. We can look at mobile in February. Alright, great work everyone. Meeting adjourned."}
]

async def generate_meeting():
    for i, line in enumerate(speakers):
        communicate = edge_tts.Communicate(line['text'], line['voice'])
        await communicate.save(f"part_{i}.mp3")
    print("Parts generated! Use ffmpeg to concatenate them into one meeting.mp3")

if __name__ == "__main__":
    asyncio.run(generate_meeting())