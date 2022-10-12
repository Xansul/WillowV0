import WillowConfig as WC
from azure.cognitiveservices.speech.audio import AudioOutputConfig
from azure.cognitiveservices.speech.speech import SpeechSynthesizer
from azure.cognitiveservices.speech.speech_py_impl import CancellationDetails
import pyttsx3 as tts
import requests
import re
import azure.cognitiveservices.speech as speechsdk
import WillowConfig
import WillowSubstrings as WS
import WillowHACommands as Wcom
import time
from playsound import playsound


#Azure SDK config
speech_config = speechsdk.SpeechConfig(subscription=WillowConfig.azure_token, region=WillowConfig.azure_region)
audio_input = speechsdk.AudioConfig(filename=WC.audio)
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
speech_config.speech_synthesis_language = "en-US"
speech_config.speech_synthesis_voice_name = "en-US-AmberNeural"
audio_out_config = AudioOutputConfig(use_default_speaker=True)
synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_out_config)

# pyttsx3 config
offline_engine = tts.init()
voices = offline_engine.getProperty("voices")
offline_engine.setProperty("voice", voices[1].id)


#setup keyword recognition (https://github.com/Azure-Samples/cognitive-services-speech-sdk/blob/b4257370e1d799f0b8b64be9bf2a34cad8b1a251/samples/python/console/speech_sample.py#L517)
def speech_recognize_keyword_locally_from_microphone():
    """runs keyword spotting locally, with direct access to the result audio"""

    # Creates an instance of a keyword recognition model. Update this to
    # point to the location of your keyword recognition model.
    model = speechsdk.KeywordRecognitionModel(WC.table)

    # The phrase your keyword recognition model triggers on.
    keyword = "Hey Willow"

    # Create a local keyword recognizer with the default microphone device for input.
    keyword_recognizer = speechsdk.KeywordRecognizer()

    done = False

    def recognized_cb(evt):
        # Only a keyword phrase is recognized. The result cannot be 'NoMatch'
        # and there is no timeout. The recognizer runs until a keyword phrase
        # is detected or recognition is canceled (by stop_recognition_async()
        # or due to the end of an input file or stream).
        result = evt.result
        if result.reason == speechsdk.ResultReason.RecognizedKeyword:
            print("RECOGNIZED KEYWORD: {}".format(result.text))
        nonlocal done
        done = True

    def canceled_cb(evt):
        result = evt.result
        if result.reason == speechsdk.ResultReason.Canceled:
            print('CANCELED: {}'.format(result.cancellation_details.reason))
        nonlocal done
        done = True

    # Connect callbacks to the events fired by the keyword recognizer.
    keyword_recognizer.recognized.connect(recognized_cb)
    keyword_recognizer.canceled.connect(canceled_cb)

    # Start keyword recognition.
    result_future = keyword_recognizer.recognize_once_async(model)
    print('Say something starting with "{}" followed by whatever you want...'.format(keyword))
    result = result_future.get()
    return result

    # Read result audio (incl. the keyword).
    #if result.reason == speechsdk.ResultReason.RecognizedKeyword:
    #    time.sleep(3) # give some time so the stream is filled
    #    result_stream = speechsdk.AudioDataStream(result)
    #    result_stream.detach_input() # stop any more data from input getting to the stream

    #    save_future = result_stream.save_to_wav_file_async(r"AudioFromRecognizedKeyword.wav")
    #    print('Saving file...')
    #    saved = save_future.get()

    # If active keyword recognition needs to be stopped before results, it can be done with
    #
    #   stop_future = keyword_recognizer.stop_recognition_async()
    #   print('Stopping...')
    #   stopped = stop_future.get()

#check for connection to HA API, speak status with offline engine (function)
def HAStatus():
    connected_response = """{"message": "API running."}"""
    response = requests.get(WC.endpoint, headers=WillowConfig.headers)
    response_text = response.text
    print(response_text)

    if response_text == connected_response:
        offline_engine.say("Connected to Home Assistant!")
        offline_engine.runAndWait()
        return True
    else:
        offline_engine.say("I'm having trouble connecting to Home Assistant.")
        offline_engine.runAndWait()

#startup
HA_status = HAStatus()
if HA_status == True:

    #bootup
    playsound(r"Resources\WillowSound1.wav")
    synthesizer.speak_text_async("Willow is ready to help!")

    running = True

    while running:

        # recognize keyword using Azure
        keyword_status = speech_recognize_keyword_locally_from_microphone()
        print(keyword_status)

        if keyword_status:

            audio_result = speech_recognizer.recognize_once_async().get()
            audio_result = audio_result.text.lower()
            print(audio_result)

            #start command search
            #light searches
            if re.search(WS.lights_substring, audio_result):

                light_entity = Wcom.FindEntity(audio_result)

                #toggle lights
                if re.search(WS.toggle_substring, audio_result):
                    Wcom.ToggleLights(light_entity)
                    continue
                
                #change light color
                elif Wcom.DoesColorExist(audio_result):
                    color = Wcom.FindColorName(audio_result)
                    Wcom.ChangeLightColor(light_entity, color)
                    print(color)
                    continue

                #change light temp
                elif re.search(r"temperature", audio_result) or re.search(r"temp", audio_result):
                    temp = Wcom.FindTempType(audio_result)
                    Wcom.ChangeLightTemp(light_entity, temp)
                    continue

            #shutdown
            elif re.search(WS.shutdown_substring, audio_result):
                break
            
            #no recognized command
            else:
                print("No command recognized")
                continue
        
            continue

    print("Keyword recognition has stopped")
