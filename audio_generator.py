import asyncio
import edge_tts

speakers = [
    {"name": "Manager", "voice": "en-US-GuyNeural", "text": "Good morning everyone. Let's get settled and focused. Today is Tuesday, January 20th, 2026. We are exactly seven days away from our hard deadline on January 27th. This Minutes of Meeting AI project is currently the highest priority for the executive team. We need a flawless end-to-end walk-through of the entire pipeline today. We will track every single millisecond—from the moment a user hits the 'Generate' button on our new UI until that final structured JSON is returned by Ollama. Sonia, you've been leading the backend stabilization effort. Let’s start with the current state of the GPU handover logic."},
    
    {"name": "Sonia", "voice": "en-GB-SoniaNeural", "text": "Thanks, Guy. On the backend, I've spent the last 48 hours refining main.py and the whisper_gpu utility. The core issue we faced last week was the CUDA Out-of-Memory error when switching from transcription to extraction. To fix this, I've formalized the release_gpu function. It now explicitly calls torch.cuda.empty_cache() and manually deletes the model variables from memory before we even initiate the POST request to the Ollama local API. This is vital because Llama 3.1 8B requires about 5.5 gigabytes of VRAM in our current quantized format, and Whisper takes another 2 to 3 gigabytes. On our standard 8 gigabyte cards, we were redlining and crashing the service constantly."},
    
    {"name": "Natasha", "voice": "en-AU-NatashaNeural", "text": "I've been monitoring those VRAM spikes closely during my stress tests on the dev server. Sonia, the cache clearing is definitely working much better than the previous iteration, but I've noticed a persistent 3 to 5-second hang-time during the handover between the models. I wanted to ask Liam—as our infrastructure lead—is that something we can actually optimize further in the Python code, or is that just the inherent hardware latency for the GPU to reallocate those massive memory blocks? If we can't reduce it, we need to ensure the user interface accounts for it."},
    
    {"name": "Liam", "voice": "en-CA-LiamNeural", "text": "Natasha, that's almost entirely hardware and PCIe bus latency. Moving the Whisper weights out of the GPU and loading the Llama weights into the active VRAM simply takes time on these consumer-grade cards. For the MVP launch on January 27th, I think 3 to 5 seconds is acceptable. However, Clara, from a security standpoint, do we have any concerns about these models being swapped in and out of memory so frequently in a multi-tenant environment?"},
    
    {"name": "Clara", "voice": "en-CA-ClaraNeural", "text": "Liam, as long as the temp files are handled correctly, we're safe. Sonia, I noticed in main.py we use a temporary file for the audio upload. Are we absolutely certain that os.remove is firing every single time? We cannot have raw meeting audio sitting in the /tmp directory if the transcription process fails halfway through. That would be a major compliance breach for our client."},
    
    {"name": "Sonia", "voice": "en-GB-SoniaNeural", "text": "I've wrapped the entire logic in a try-finally block. Even if Whisper or Ollama throws an exception, the finally block executes the os.remove on the audio_path. I've also implemented a 120-second timeout on the Ollama request to prevent a hanging process from keeping a file lock indefinitely. If it fails, the file is deleted, and the user gets a structured error message."},
    
    {"name": "Prabhat", "voice": "en-IN-PrabhatNeural", "text": "Speaking of the interface, the UI is mostly ready. I’ve implemented the Tailwind CSS layout we discussed. I also added the logic where the upload box changes color and displays the filename once a file is selected. Users were getting confused before, but now they get immediate visual feedback. For Natasha's concern about the 5-second gap, I'll add a 'Memory Handover' status message so the user knows the AI is switching from its 'ears' to its 'brain'."},
    
    {"name": "Liam", "voice": "en-CA-LiamNeural", "text": "Prabhat, that's great for the visual side, but what about the backend concurrency? If two managers upload a meeting at the same time, we only have one GPU card. The second request will fail the CUDA lock immediately."},
    
    {"name": "Prabhat", "voice": "en-IN-PrabhatNeural", "text": "That's exactly why I'm setting up a Redis queue this week. I'll have a prototype by Wednesday. For the January 27th launch, we will stick to a single-processing stream to ensure stability, but the UI will query the Redis state. If the GPU is busy, the user will see a 'Queue Position' instead of an error message. It keeps the experience smooth without needing more hardware yet."},
    
    {"name": "Manager", "voice": "en-US-GuyNeural", "text": "Let's talk about the output quality. Roger, you’ve been testing the JSON extraction. Are we 100% sure about sticking with Llama 3.1 8B, or should we try a different quantized version for better reasoning?"},
    
    {"name": "Roger", "voice": "en-US-RogerNeural", "text": "We tested the 70B model, but even with high quantization, the inference time per meeting was over 4 minutes. The 8B-instruct-q4_K_M version in Ollama is giving us near-instant extraction once the transcript is ready. Our accuracy on identifying action items is around 94%, which is higher than the client's requirement of 90%. I’m also using Edge TTS to generate synthetic noise-heavy meetings to simulate real-world office environments. Natasha, I'll send you those noisy audio files by Thursday afternoon so you can run the final stress tests."},
    
    {"name": "Natasha", "voice": "en-AU-NatashaNeural", "text": "How 'noisy' are we talking, Roger? Our Whisper 'small' model is good, but if there's heavy background chatter or coffee machine noise, the word error rate might climb. Have you adjusted the vad_filter parameters in whisper_gpu.py to compensate for office background noise?"},
    
    {"name": "Sonia", "voice": "en-GB-SoniaNeural", "text": "I've actually already accounted for that in the transcription settings. Also, I can add a 'Download PDF' button to the results page by Friday. I'll use a simple client-side library to convert the JSON data into a formatted document. It will format the tasks, decisions, and summary into a clean corporate template without needing any backend changes."},
    {"name": "Manager", "voice": "en-US-GuyNeural", "text": "Okay, final recap. Prabhat, you have the Redis queue and 'Server Busy' UI by Wednesday. Sonia, you're adding the PDF export by Friday. Roger, you're delivering noise-test files by Thursday. Natasha and Clara, your final QA and Security sign-off is due Thursday evening. We are not supporting mobile for the MVP—stick to desktop web. If we hit these marks, we go live on January 27th. Great work, everyone. Meeting adjourned!"}
]

async def generate_meeting():
    for i, line in enumerate(speakers):
        communicate = edge_tts.Communicate(line['text'], line['voice'])
        await communicate.save(f"part_{i}.mp3")
    print("Parts generated! Use ffmpeg to concatenate them into one meeting.mp3")

if __name__ == "__main__":
    asyncio.run(generate_meeting())