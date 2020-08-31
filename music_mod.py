import wave
import youtube_dl
import os

volume = 0.4

youtube2name = {"https://youtu.be/SF27B_HIBkM": "file128_audio", # The Neverhood Theme
"https://youtu.be/_3ecL4pQkIA": "file146_audio", # Potatoes, Tomatoes, Gravy and Peas
"https://youtu.be/_kvZNWZpOPI": "file138_audio", # Skat Radio
"https://youtu.be/cLp5Npzg2wY": "file135_audio", # Operator Plays A Little Ping Pong
"https://youtu.be/XSJwiTWBOkM": "file130_audio", # Everybody Way Oh!
"https://youtu.be/YD9avMsX3u0": "file127_audio", # Cough Drops
"https://youtu.be/zDrVzwnAtWU": "file139_audio", # Southern Front Porch Whistler
"https://youtu.be/dEVzasyzJNI": "file126_audio", # Confused And Upset
"https://youtu.be/F1YV0exck0U": "file132_audio", # Klaymen's Theme
"https://youtu.be/I__iHJMJX9c": "file140_audio", # Triangle Square
"https://youtu.be/b3NRdc6_Bhc": "file131_audio", # Homina Homina
"https://youtu.be/bNbZCRsRQJA": "file133_audio", # Lowdee Huh
"https://youtu.be/Og4yWj6tsug": "file129_audio", # Dum Da Dum Doi Doi
"https://youtu.be/uCqwE9iV0Fw": "file136_audio", # Rock And Roll Dixie
"https://youtu.be/xHJ4QZ8pmr0": "file134_audio" # Olley Oxen Free
}

def download(url, name):
    ydl_opts = {
        'format': 'bestaudio[ext=webm]',
        'outtmpl': f'mod_tmp/{name}.mp3',
        'noplaylist': True,
        'continue_dl': True,
        'postprocessor_args': [
            '-ar', '22050', '-ac', '1', '-filter:a', f'volume={volume}'
        ],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            }]
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.cache.remove()
            info_dict = ydl.extract_info(url, download=False)
            ydl.prepare_filename(info_dict)
            ydl.download([url])
            return True
    except Exception:
        return False

os.makedirs("mod_dir/", exist_ok=True)

for i in youtube2name:
    fileName = youtube2name[i]
    print("Patching: {}".format(fileName))
    out_file = "files/"+fileName

    youtube_url = i
    download(youtube_url, fileName)

    waveFile = wave.open("mod_tmp/"+fileName+".wav", 'r')
    outFile = open(out_file, "wb")

    length = waveFile.getnframes()
    for i in range(0,length):
        waveData = waveFile.readframes(1)
        outFile.write(waveData)

    outFile.close()
