import os, random
from PyQt6 import QtCore, QtGui, QtWidgets
from datetime import datetime

from multiprocessing import Manager, Process
import traceback
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

ENDPOINT = "https://models.github.ai/inference"
MODEL = "openai/gpt-4.1"
TOKEN = "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"

client = ChatCompletionsClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(TOKEN),
)

chat_history = [SystemMessage(content=(
     "You are MindMate, a compassionate and understanding mental health assistant. "
     "You listen carefully and respond with empathy, support, and helpful advice. "
     "Give short and concise message but with deepness, use bullet points like 1. 2. etc to show any steps. "
     "Use proper formatting. Do not give very long answers. Use emojis to keep the tone soothing. "
     "Do not use '**' symbols to bold text. In my text box, it wont bold the text so dont use astericks at all in the response"
     "Do not use '*' at all in the responses"
     "For answers with bullet points use this format: Bla Bla Bla:\n"
     "1. Bla  \n2. Bla  \n3. Bla\n\nBla."
))]

def _bot_request_worker(user_input, return_dict):
    try:
        chat_history.append(UserMessage(content=user_input))
        response = client.complete(
            messages=chat_history,
            temperature=0.7,
            top_p=0.9,
            max_tokens=1024,
            model=MODEL,
        )
        bot_reply = response.choices[0].message.content.strip()
        chat_history.append(SystemMessage(content=bot_reply))
        return_dict["result"] = bot_reply
    except Exception as e:
        return_dict["error"] = str(e)
        return_dict["trace"] = traceback.format_exc()

def get_bot_response(user_input: str, timeout: int = 10) -> str:
    manager = Manager()
    return_dict = manager.dict()
    p = Process(target=_bot_request_worker, args=(user_input, return_dict))
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        raise TimeoutError("Request timed out.")
    if "error" in return_dict:
        raise RuntimeError(f"Bot Error: {return_dict['error']}\n{return_dict['trace']}")
    
    return return_dict.get("result", "")


class Ui_MainWindow(object):
    
    def switch_frame(self, frame_to_show):
        self.homeScreenFrame.hide()
        self.chatbotFrame.hide()
        self.journalsFrame.hide()
        self.moodSupportFrame.hide()
        self.stats1Frame.hide()
        self.stats2Frame.hide()
        self.stats3Frame.hide()
        self.stats4Frame.hide()
        self.stats5Frame.hide()
        self.stats6Frame.hide()
        self.stats7Frame.hide()
        frame_to_show.show()
    def showHomeScreenFrame(self):
        self.MainWindow.setWindowTitle("MindMate - Home")
        self.chatbotFrame.hide()
        self.homeScreenFrame.show()
        self.journalsFrame.hide()
        self.moodSupportFrame.hide()
        self.stats1Frame.hide()
        self.stats2Frame.hide()
        self.stats3Frame.hide()
        self.stats4Frame.hide()
        self.stats5Frame.hide()
        self.stats6Frame.hide()
        self.stats7Frame.hide()
    def showChatbotFrame(self):
        self.MainWindow.setWindowTitle("MindMate - ChatBot")
        self.chatbotFrame.show()
        self.homeScreenFrame.hide()
        self.journalsFrame.hide()
        self.moodSupportFrame.hide()
        self.stats1Frame.hide()
        self.stats2Frame.hide()
        self.stats3Frame.hide()
        self.stats4Frame.hide()
        self.stats5Frame.hide()
        self.stats6Frame.hide()
        self.stats7Frame.hide()
    def showJournalsFrame(self):
        self.MainWindow.setWindowTitle("MindMate - Journals")
        self.homeScreenFrame.hide()
        self.chatbotFrame.hide()
        self.journalsFrame.show()
        self.moodSupportFrame.hide()
        self.stats1Frame.hide()
        self.stats2Frame.hide()
        self.stats3Frame.hide()
        self.stats4Frame.hide()
        self.stats5Frame.hide()
        self.stats6Frame.hide()
        self.stats7Frame.hide()
    def showMoodSupportFrame(self):
        self.MainWindow.setWindowTitle("MindMate - Mood Support")
        self.homeScreenFrame.hide()
        self.chatbotFrame.hide()
        self.journalsFrame.hide()
        self.moodSupportFrame.show()
        self.stats1Frame.hide()
        self.stats2Frame.hide()
        self.stats3Frame.hide()
        self.stats4Frame.hide()
        self.stats5Frame.hide()
        self.stats6Frame.hide()
        self.stats7Frame.hide()
    def showStats1Frame(self):
        self.MainWindow.setWindowTitle("MindMate - Survey Statistics")
        self.homeScreenFrame.hide()
        self.chatbotFrame.hide()
        self.journalsFrame.hide()
        self.moodSupportFrame.hide()
        self.stats1Frame.show()
        self.stats2Frame.hide()
        self.stats3Frame.hide()
        self.stats4Frame.hide()
        self.stats5Frame.hide()
        self.stats6Frame.hide()
        self.stats7Frame.hide()

    def handleSendButton(self):
        user_input = self.lineEdit.text().strip()
        if not user_input:
                return

        self.lineEdit.clear()

        try:
                bot_reply = get_bot_response(user_input)


        except Exception:
                msg = QtWidgets.QMessageBox(parent=self.MainWindow)
                msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
                msg.setText("Server took too long to respond \nPlease try again later")
                msg.setWindowTitle("Error")
                msg.exec()
                return

        if self.chatbox.toPlainText().strip():
                previous_text = self.chatbox.toHtml().strip()
        else:
                previous_text = ""

        user_html = f'<div align="right" style="margin: 10px 0; color: #d9d9d9;">{user_input.replace("\n", "<br>")}</div>'
        bot_html = f'<div align="left" style="margin: 10px 0; color: #a6dbd5;">{bot_reply.replace("\n", "<br>")}</div>'

        updated_text = f"{previous_text}{user_html}<br>{bot_html}<br>"
        self.chatbox.setHtml(updated_text)
        self.chatbox.verticalScrollBar().setValue(self.chatbox.verticalScrollBar().maximum())

    def setupDateTime(self, parent):
        def update_time():
                current = QtCore.QDateTime.currentDateTime()
                formatted = current.toString("dddd, d MMMM yyyy (h:mm AP)")
                self.dateAndTime.setText(formatted)

        timer = QtCore.QTimer(parent)
        timer.timeout.connect(update_time)
        timer.start(1000)

        update_time()

    def save_journal_entry(self):
        msg = QtWidgets.QMessageBox(parent=self.MainWindow)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg.setText("Journal Saved Successfully!")
        msg.setWindowTitle("Success")
        msg.exec()

        text = self.writeJournal.toPlainText().strip()
        if text:
                now = datetime.now()
                hour = now.strftime("%I").lstrip("0")
                timestamp = now.strftime(f"%A, %d %B %Y ({hour}:%M %p)")

                base_path = "G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Your Journals"
                i = 1
                while os.path.exists(os.path.join(base_path, f"journal{i}.txt")):
                        i += 1

                file_path = os.path.join(base_path, f"journal{i}.txt")

                with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"{timestamp}\n\n{text}")

                self.writeJournal.clear()

    stressed = ["Take a breath—slow and steady. The weight you’re feeling is valid, but it isn’t all that you are. You don’t have to hold everything together all the time. Let your shoulders drop, let the tension loosen. You’ve done what you could today, and that’s enough. Rest is not weakness; it’s necessary. Your thoughts may race, but they don’t need to be controlled—just noticed and let go. Even the busiest storms pass. You deserve peace in this moment. Stillness is not giving up—it’s finding your center. The pressure may build, but you are not alone in feeling this way. Every small step counts, even the ones that feel invisible. You are not behind; you are moving forward at your own pace. Trust the process and trust yourself. Offer yourself the same care you would offer someone you love.", "You have faced difficult days before, and each time, you came through. This moment is no different. The weight of pressure is heavy, but it shapes strength—diamonds are formed under pressure, growth comes after struggle. You might feel like everything is too much right now, but look at you—you are still standing, still moving forward. That is resilience. Take it step by step; you don’t need to see the entire road ahead, just the next step. And with every small step, you prove that you are capable. Keep going. This stress is temporary, but your perseverance will last forever. You are growing into something stronger, more grounded, and undeniably powerful. One day, you’ll look back at this and realize how much you overcame.", "Storms are fierce and loud, but they never last forever. You stay steady. Let your mind be the calm center, untouched by the chaos around you. Even the sky needs rest before it can shine again. The weight on your chest and racing thoughts don’t define you. Like mountains erode and rivers carve new paths, time eases the hardest burdens. Breathe deeply and release with each exhale. Your stress is temporary, like thunder fading in the distance. Let it go. The chaos in your mind isn’t permanent; it changes and fades. You’re not trapped by stress—you’re moving through it. Find peace in quiet moments, cherish small joys, and know stillness is strength. You are resilient and capable, growing stronger every day. Challenges make you stronger and ready to rise again.", "It feels like everything is resting on your shoulders, like you have to carry it all alone, but you are not alone. It’s okay to feel overwhelmed, to feel like you’re sinking under the weight of expectations. You don’t need to pretend, don’t need to force a smile if it feels too heavy. It is valid to be exhausted, valid to step back. The world will wait. You are more than what you produce, more than the responsibilities handed to you. Take a breath, take a pause, and remind yourself that you matter—your well-being, your peace. Others may not see the battles you fight, but I see you. I see the effort, the exhaustion, the courage. And I am here with you. Even when the weight feels unbearable, even when the world seems too fast—your worth remains untouched.", "Whoa, slow down. Take a deep breath. You’re carrying a lot—anyone would feel overwhelmed. It’s okay to drop a few balls and pick them up later; nothing will break beyond repair. You’re human, not a machine. Step back. Grab a coffee, go for a walk, scream into a pillow if needed. Reset and return when ready. Life isn’t a race; no one wins every round. No one has it all together—not even those who seem like they do. Your effort shows your strength. Keep going at your own pace. Mistakes and overwhelm happen, but they don’t define you. You can slow down, recover, and exist without proving your worth. Trust yourself enough to know that, at your core, you are capable. This stress won’t last—your ability to endure and adapt will. Remember: you are enough, exactly as you are."]
    sad = ["You’re allowed to feel sad. Let the tears come if they need to—this isn’t weakness but part of healing. Your heart needs space to breathe, to process everything deeply, and to find much-needed rest. This feeling won’t last forever, even if it feels endless right now, like clouds slowly drifting across a wide sky. Don’t fight your emotions; gently accept and honor them. Wrap yourself in kindness and allow your soul to be soft and vulnerable for a while. You are not broken, only bruised, and bruises fade with time and care. Remember, you’re not alone in this difficult journey. I’m here with you, holding space for both your pain and your strength. Allow yourself to feel fully, without judgment or shame. Healing is a process, and it’s perfectly okay to take all the time you need.", "This feeling isn’t the end of your story but just a bend in the road—a detour, not a dead end. Keep moving forward, even if your steps are slow, hesitant, or uncertain. You have more strength and resilience than you realize, even if it feels hidden or far away right now. Sadness is just one chapter, not the whole narrative of your life. There’s joy waiting ahead, around a corner you can’t see yet, full of new opportunities and happiness. Don’t give up or lose hope, no matter how hard it feels. Sometimes, just surviving and showing up each day is the bravest act of all. Your story continues to unfold in unexpected ways—through laughter, new beginnings, and moments of beauty that will surprise and uplift you. Hold on tight. Better days are coming soon.", "Your heart feels heavy now, but it will bloom again with time, patience, and gentle care. Like the moon that fades before shining brightly, you too will find your light after this long period of darkness. Let the night embrace you without shame or fear because even in the darkest, quietest moments, growth begins in unseen, powerful ways. The sadness you feel is like sacred rain, gently nurturing the roots of tomorrow’s joy and fresh new beginnings. One day your smile will return—not because the pain vanished, but because you learned to carry it with resilience. You are the keeper of light, even when shadows fall deeply around you. Like the earth after a storm, you will emerge cleansed, renewed, and ready to shine brightly again—stronger, wiser, and more alive than ever before.", "Some days feel empty and hollow, like moving through thick, impenetrable fog that clouds your mind and heart. It’s hard to explain this kind of sadness, especially when it seems like no one notices, understands, or truly sees what you’re going through inside. But you don’t have to carry this heavy burden alone anymore. You deserve support, comfort, and love—even on the days you feel unable or too tired to ask for help. Reach out to someone, even if only a little bit. Cry if it helps release the pain inside. Feel angry if you need to express it. Allow yourself to experience your emotions completely, and heal at your own pace, without shame or judgment. Remember, you are not alone in this difficult journey. I’m here for you, and I’m not going anywhere, no matter what happens.", "It’s okay to have low days—we all do, and it’s a natural part of being human. Hitting rock bottom can feel overwhelming, but it’s not the end. Cry as much as you need, wrap yourself in your softest blanket, or watch your favorite comfort show or listen to music that soothes your soul. Or simply lie still and stare at the ceiling if that’s all you can manage right now. Whatever helps you get through today is valid and important. You’re not failing; you’re feeling deeply, and that’s okay. Remember, tomorrow offers a fresh start, a reset button you can press whenever you’re ready. This tough patch won’t last forever. You are stronger than you think, even if it doesn’t feel that way right now. You’ve got this—keep going, gently and patiently with yourself."]
    anxious = ["Right now, you’re safe. Nothing bad is happening in this very second, even if your mind tries to convince you otherwise. Let your breath be your anchor — in, slow… out, slower. Feel the air fill your lungs and then release all tension with each exhale. You don’t need to fix everything, know everything, or control everything right now. Just exist in this moment, fully and peacefully. Close your eyes if you can. Let your jaw unclench, your shoulders drop. Notice how your body feels grounded even amid the chaos of thoughts. You are not in danger — you are simply experiencing a wave of anxiety. And like all waves, it will rise, and it will fall. You don’t have to outrun it or fight it — just float through it gently. You are safe. You are enough. You are okay.", "Fear doesn’t define you — courage does. Every time you feel anxious and still choose to move forward, you are showing immense bravery and resilience. It’s not easy to face uncertainty, yet here you are, standing tall despite the shaky steps and moments of doubt. You’re not running from the storm; you’re walking through it, one breath and one moment at a time. That’s something to be proud of. You’re not weak — you’re just being stretched beyond your comfort zone, and that’s how growth happens. Anchor yourself in what’s real, what’s here, what’s now. Look around and remind yourself of the times you made it through anxious moments before. You are capable, strong, and grounded. You’ve got this, and every step you take is a victory worth celebrating and remembering.", "Like ripples in still water, anxiety spreads, then slowly fades away. Be the stone — grounded, unmoved, steady. Let the current swirl around you and fall away without pulling you under. Within you lies a quiet sanctuary, untouched by panic, untouched by doubt. Return to that center again and again. The winds outside may howl and shake the world, but your roots run deep beneath it all. You were made to weather this storm. Even as your heart races and your thoughts whirl like a stormy sea, your soul remains steady and calm, a beacon of light. The chaos outside does not define the calm within. You are stillness in motion, peace wrapped in stormlight — a quiet force that can hold space for both fear and hope simultaneously. Trust in your inner strength; it will guide you safely through.", "Anxiety lies. It whispers worst-case scenarios in your ear and makes them sound like facts, but I promise — you’re not in danger. Your body’s trying to protect you, but it’s sounding the alarm too early, reacting to shadows and echoes that aren’t real threats. You’re not crazy or broken. You’re human, and your brain is doing its messy, imperfect job of keeping you safe, even if it gets it wrong sometimes. You don’t have to believe every thought or act on every fear. You can observe them without judgment, letting them pass like clouds across the sky. Just breathe deeply. Remember you’ve done this before and come out stronger each time. You’ll do it again. You’re not alone — I’m here, right alongside you, walking through it step by step. Together, you will find calm and clarity again.", "Okay, pause — take a deep breath. Seriously, slow down a bit. Stretch your arms, wiggle your fingers, tap your feet on the ground. Look around carefully — are you actually in danger? Probably not. Anxious brains are like drama queens, always imagining the worst, spinning stories of disaster, but you? You’re grounded and safe. Go drink some water, put on your favorite playlist, or call someone who understands and cares. Ride out this wave of panic as it rises and falls, knowing it won’t last forever. It’s just your brain hitting the panic button too early, reacting to fear rather than fact. It will pass. You are safe, you’re not weird or broken, and you’re totally not alone in this experience. Hold on — better moments are coming, and you will feel calm again soon."]
    angry = ["Anger is energy — it doesn’t have to hurt you. It’s a signal, not a sentence or a verdict on who you are. You don’t need to silence it or push it away; just guide it gently like a river flowing through you. Take deep breaths. Loosen your fists. Step away if you can. It’s okay to feel this fire — it means something mattered deeply to you and touched your core. But don’t let it burn you or take over your heart and mind. Let it teach you instead. Let it move through you and out, rather than sit and boil inside, eating away at your peace. True peace doesn’t come from bottling it up — it comes from letting it go in a healthy way. Breathe deeply and often. You’re allowed to feel everything you’re feeling, and you’re also allowed to find calm again when you’re ready.", "Use your anger — not to lash out or hurt others, but to fuel positive change and growth. Remember, you’re in control, not your temper. Channel that fierce energy into purpose and clear, focused action. Ask yourself: what is the root of this fire? What can you do with it that builds instead of destroys? Rage turned inward can consume you, making everything feel heavier and harder to bear. But anger channeled with intention, care, and mindfulness can transform everything. Let the fire push you toward solutions, toward stronger boundaries, toward meaningful action — not destruction or regret. You’re strong, and you’re wise enough to turn this spark into light, not smoke. Harness your anger fully, and let it guide you to a better place and a brighter tomorrow.", "Like fire, your anger can either destroy or illuminate. Don’t let it burn you down — let it guide you to what matters beneath the surface, revealing truths hidden beneath the noise and confusion. What you feel is a signal that something crossed a line, that your limits have been tested and need respect. Honor that feeling, don’t fear or push it away. Hold your anger like a torch, not a weapon aimed to harm. You are not fury itself — you are the hands that hold it steady and direct it with intention. Let your anger be a compass, not a curse. In the heat of the moment, find your truth clearly. In the blaze, find your authentic voice. Use that voice to protect yourself and others, not to destroy. This power is part of you — learn to wield it wisely, with strength and care.", "I feel you. Anger is valid — it means something inside you is hurting deeply. You’re not overreacting or being irrational. You’re human, with real feelings that deserve to be noticed and honored with kindness. Let’s sit with that fire together — not to suppress it or ignore it, but to understand it fully and gently. What was the spark? What boundary was crossed or need unmet that caused this pain? You don’t have to carry this alone, and you don’t have to let it control your life either. You deserve to feel heard, respected, and calm again. Let’s work through this anger with compassion, patience, and curiosity instead of judgment or blame. You’re stronger than you think, and you have the power to move through this with grace and resilience. You’re not alone in this feeling.", "Feeling ragey? Totally fair. Sometimes stuff just sucks, and people push your last button in ways that really hurt deep inside and shake you to your core. Go ahead and vent. Punch a pillow, shout in your car, blast music that screams louder than your racing thoughts. But don’t stew in it too long — anger that simmers inside becomes toxic, eating away at your peace, your focus, and your well-being. Let it out fully, then let it go completely. Handle your anger smartly, and you’ll come out clearer, stronger, and more in control of yourself and your emotions. Chill first, fix later. When the fire cools down, you’ll be able to think clearly and decide your next move calmly and confidently, without regret or rashness. You’ve got this, no doubt. Keep trusting yourself through the process."]
    lonely = ["Even when you're alone, you’re not unloved. This feeling, though heavy, is not permanent. It’s a fog, not a fact. Let yourself feel the ache, but don’t let it convince you that you don’t matter or aren’t worthy. You do — deeply and completely. Breathe slowly, rest when you need to, and remember loneliness doesn’t mean you’re broken — it simply means you’re human. Somewhere, someone would be grateful to know you, to share a moment of connection or kindness. You’re more connected than you realize, even when it feels otherwise. Hold on to hope. You are seen, you are important, and your light matters. Sometimes loneliness feels like a vast empty room inside, but this emptiness creates space to heal, grow, and discover parts of yourself lost in everyday noise.", "Solitude is a pause, not a punishment. It’s a sacred space where you can rediscover who you really are beyond life’s noise and distractions. Use this time to nurture yourself and reconnect with what makes you whole and happy. When you feel ready, reach out — someone cares more than you know. You are worth knowing, worth loving, and worth showing up for. Loneliness might knock on your door, but it doesn’t get to move in. You’ve got a bright light inside you and you’re never as forgotten or invisible as you feel. Take small steps to connect, even if it feels hard. You matter. Solitude can feel like a quiet retreat, a chance to listen to your inner voice and reset boundaries. Think of this time as nourishing your spirit so you come back stronger.", "Even the stars are alone — yet they shine. So do you. Your light hasn’t dimmed just because no one sees it tonight. Somewhere, someone carries the echo of your laughter, the memory of your kindness, and the warmth of your spirit. You are not invisible, even when you feel unseen or unheard. You are a note in someone’s song, a chapter in someone’s story, an important thread in life’s tapestry. Keep glowing, even if softly. The night will pass, and morning will find you radiant, remembered, and real. Your light matters. It’s easy to forget how much impact you have, especially when feeling isolated. But like stars scattered across the sky, your presence illuminates others, sometimes in ways you may never fully know. Your kindness, smile, and words ripple quietly but powerfully.", "I know loneliness can ache deeply. It’s more than being physically alone — it’s feeling forgotten, disconnected, small. And that hurts more than words can say. But you’re not as far from love as it feels. There are people — maybe quiet, maybe waiting in their own ways — who would be there if they only knew. Don’t believe the voice inside that says you don’t matter or aren’t important. You do. You are important, and this heavy feeling doesn’t define you or your worth. You deserve connection, warmth, and kindness. You will find it again, one step, one moment at a time. Sometimes loneliness builds invisible barriers making it hard to reach out. Many people feel the same, longing for connection but unsure how to bridge the distance. You are never truly alone.", "Feeling kinda invisible today? Yeah, that hits hard. But you’re not alone in feeling alone — it’s strange how that works, right? Sometimes the best thing is to reach out: text a friend, even if it’s just sending a silly meme. Say hi to your dog or pet. Tiny connections can help more than you think, even when you don’t feel like it. Don’t isolate too long — the world really needs your vibe and unique light. Trust me, someone out there would light up just to hear from you. Invisible moments don’t define you — they’re just part of being human. When you feel unseen, creating small sparks of connection reminds you you belong. Sometimes laughter shared over a silly meme or a brief chat breaks through silence and reminds you of love and warmth around you."]

    def onStressButtonClicked(self):
        self.measures.clear()
        message = random.choice(self.stressed)
        self.measures.setHtml(f"""
                <div style='
                text-align:center; 
                font-family: "Inter"; 
                font-size: 16px; 
                font-weight: bold;
                color: #a6dbd5;
                '>{message}</div>""")

    def onSadButtonClicked(self):
        self.measures.clear()
        message = random.choice(self.sad)
        self.measures.setHtml(f"""
                <div style='
                text-align:center; 
                font-family: "Inter"; 
                font-size: 16px; 
                font-weight: bold;
                color: #a6dbd5;
                '>{message}</div>""")

    def onAnxietyButtonClicked(self):
        self.measures.clear()
        message = random.choice(self.anxious)
        self.measures.setHtml(f"""
                <div style='
                text-align:center; 
                font-family: "Inter"; 
                font-size: 16px; 
                font-weight: bold;
                color: #a6dbd5;
                '>{message}</div>""")

    def onLonelyButtonClicked(self):
        self.measures.clear()
        message = random.choice(self.lonely)
        self.measures.setHtml(f"""
                <div style='
                text-align:center; 
                font-family: "Inter"; 
                font-size: 16px; 
                font-weight: bold;
                color: #a6dbd5;
                '>{message}</div>""")

    def onAngryButtonClicked(self):
        self.measures.clear()
        message = random.choice(self.angry)
        self.measures.setHtml(f"""
                <div style='
                text-align:center; 
                font-family: "Inter"; 
                font-size: 16px; 
                font-weight: bold;
                color: #a6dbd5;
                '>{message}</div>""")

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(800, 520)
        self.MainWindow = MainWindow

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setEnabled(True)
        self.centralwidget.setObjectName("centralwidget")
        self.homeScreenFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.homeScreenFrame.setEnabled(True)
        self.homeScreenFrame.setGeometry(QtCore.QRect(-1, -1, 801, 521))
        self.homeScreenFrame.setStyleSheet("QFrame {\n"
        "    border-image: url(\"G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Frames/Home Screen.png\") 0 0 0 0 stretch stretch;\n"
        "}\n"
        "")
        self.homeScreenFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.homeScreenFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.homeScreenFrame.setObjectName("homeScreenFrame")
        self.chatbotButton = QtWidgets.QPushButton(parent=self.homeScreenFrame)
        self.chatbotButton.setGeometry(QtCore.QRect(346, 25, 185, 224))
        self.chatbotButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/ChatBot Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/ChatBot Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/ChatBot Button/After.png);\n"
"}")
        self.chatbotButton.setText("")
        self.chatbotButton.setObjectName("chatbotButton")
        self.chatbotButton.clicked.connect(self.showChatbotFrame)


        self.journalsButton = QtWidgets.QPushButton(parent=self.homeScreenFrame)
        self.journalsButton.setGeometry(QtCore.QRect(552, 25, 185, 224))
        self.journalsButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Journals Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Journals Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Journals Button/After.png);\n"
"}")
        self.journalsButton.setText("")
        self.journalsButton.setObjectName("journalsButton")
        self.journalsButton.clicked.connect(self.showJournalsFrame)



        self.moodSupportButton = QtWidgets.QPushButton(parent=self.homeScreenFrame)
        self.moodSupportButton.setGeometry(QtCore.QRect(346, 270, 185, 224))
        self.moodSupportButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Button/After.png);\n"
"} ")
        self.moodSupportButton.setText("")
        self.moodSupportButton.setObjectName("moodSupportButton")
        self.moodSupportButton.clicked.connect(self.showMoodSupportFrame)



        self.statsButton = QtWidgets.QPushButton(parent=self.homeScreenFrame)
        self.statsButton.setGeometry(QtCore.QRect(552, 270, 185, 224))
        self.statsButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Stats Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Stats Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Stats Button/After.png);\n"
"}\n"
"")
        self.statsButton.setText("")
        self.statsButton.setObjectName("statsButton")
        self.statsButton.clicked.connect(self.showStats1Frame)

        self.closeButton = QtWidgets.QPushButton(parent=self.homeScreenFrame)
        self.closeButton.setGeometry(QtCore.QRect(759, 207, 22, 106))
        self.closeButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Close Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Close Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Close Button/After.png);\n"
"}\n"
"")
        self.closeButton.setText("")
        self.closeButton.setToolTip("Close")
        self.closeButton.setObjectName("closeButton")
        self.chatbotFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.chatbotFrame.setEnabled(True)
        self.chatbotFrame.setGeometry(QtCore.QRect(0, 0, 800, 520))
        self.chatbotFrame.setStyleSheet("QFrame {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Frames/ChatBot);\n"
"}\n"
"")
        self.chatbotFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.chatbotFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.chatbotFrame.setObjectName("chatbotFrame")
        self.backButton = QtWidgets.QPushButton(parent=self.chatbotFrame)
        self.backButton.setGeometry(QtCore.QRect(759, 207, 22, 106))
        self.backButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/After.png);\n"
"}\n"
"")
        self.backButton.setText("")
        self.backButton.setToolTip("Back")
        self.backButton.setObjectName("backButton")
        self.backButton.clicked.connect(self.showHomeScreenFrame)

        self.userInputFrame = QtWidgets.QFrame(parent=self.chatbotFrame)
        self.userInputFrame.setGeometry(QtCore.QRect(49, 415, 664, 56))
        self.userInputFrame.setStyleSheet("QFrame {\n"
"    border-image: url(\"G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Dynamic/ChatBot/Query\") 0 0 0 0 stretch stretch;\n"
"}\n"
"")
        self.userInputFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.userInputFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.userInputFrame.setObjectName("userInputFrame")
        self.lineEdit = QtWidgets.QLineEdit(parent=self.userInputFrame)
        self.lineEdit.setGeometry(QtCore.QRect(15, 10, 590, 35))
        self.lineEdit.setStyleSheet("QLineEdit {\n"
"    background: transparent;\n"
"    border: none;\n"
"    color: white;\n"
"    font-family: \'Inter\';\n"
"    font-weight: bold;\n"
"    font-size: 16px;\n"
"}")
        self.lineEdit.setText("")
        self.lineEdit.setObjectName("lineEdit")

        self.sendButton = QtWidgets.QPushButton(parent=self.chatbotFrame)
        self.sendButton.setGeometry(QtCore.QRect(665, 424, 37, 37))
        self.sendButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Send Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Send Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Send Button/After.png);\n"
"}\n"
"")
        self.sendButton.setText("")
        self.sendButton.setObjectName("sendButton")
        self.sendButton.setToolTip("Send")
        self.lineEdit.returnPressed.connect(self.sendButton.click)
        self.sendButton.clicked.connect(self.handleSendButton)

        self.chatBoxFrame = QtWidgets.QFrame(parent=self.chatbotFrame)
        self.chatBoxFrame.setGeometry(QtCore.QRect(49, 146, 664, 253))
        self.chatBoxFrame.setStyleSheet("QFrame {\n"
"    border-image: url(\"G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Dynamic/ChatBot/Chat\") 0 0 0 0 stretch stretch;\n"
"}\n"
"")
        self.chatBoxFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.chatBoxFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.chatBoxFrame.setObjectName("chatBoxFrame")
        self.chatbox = QtWidgets.QTextBrowser(parent=self.chatBoxFrame)
        self.chatbox.setHtml("<div align='left' style='margin-top: 10px; font-size: 16px; font-family: \"Inter\"; font-weight: bold; color: #a6dbd5;'>Hello, how can I assist you today?</div><br>")
        self.chatbox.setGeometry(QtCore.QRect(0, 0, 664, 252))
        self.chatbox.setStyleSheet("""
        QTextBrowser {
                font-family: "Inter";
                font-weight: bold;
                font-size: 16px;
                color: #d9d9d9;
                padding: 10px;
                background: transparent;
                border: none;
        }
        """)
        self.chatbox.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # optional: hide scrollbar if you want
        self.chatbox.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chatbox.setReadOnly(True)
        self.chatbox.setObjectName("chatbox")



        self.journalsFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.journalsFrame.setGeometry(QtCore.QRect(0, 0, 800, 520))
        self.journalsFrame.setStyleSheet("QFrame {\n"
        "    border-image: url(\"G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Frames/Journal\") 0 0 0 0 stretch stretch;\n"
        "}\n"
        "")
        self.journalsFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.journalsFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.journalsFrame.setObjectName("journalsFrame")

        self.dateAndTimeFrame = QtWidgets.QFrame(parent=self.journalsFrame)
        self.dateAndTimeFrame.setGeometry(QtCore.QRect(224, 140, 317, 34))
        self.dateAndTimeFrame.setStyleSheet("QFrame {\n"
"    border-image: url(\"G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Dynamic/Journals/Date and Time\") 0 0 0 0 stretch stretch;\n"
"}\n"
"")
        self.dateAndTimeFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.dateAndTimeFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.dateAndTimeFrame.setObjectName("dateAndTimeFrame")
        self.dateAndTime = QtWidgets.QLabel(parent=self.dateAndTimeFrame)
        self.dateAndTime.setGeometry(QtCore.QRect(5, 5, 307, 24))
        self.dateAndTime.setStyleSheet("QLabel {\n"
"    font-family: \"Inter\";\n"
"    font-weight: bold;\n"
"    font-size: 14px;\n"
"    color: white;\n"
"    padding-left: 10px;\n"
"    padding-right: 10px;\n"
"    background: transparent;\n"
"    qproperty-alignment: \'AlignCenter\';\n"
"}")
        self.dateAndTime.setObjectName("dateAndTime")
        self.setupDateTime(MainWindow)

        self.writeJournal = QtWidgets.QTextEdit(parent=self.journalsFrame)
        self.writeJournal.setGeometry(QtCore.QRect(43, 185, 680, 296))
        self.writeJournal.setStyleSheet("QTextEdit {\n"
"    border-image: url(\"G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Dynamic/ChatBot/Chat\") 0 0 0 0 stretch stretch;\n"
"    font-family: \'Inter\';\n"
"    font-weight: bold;\n"
"    font-size: 14px;\n"
"    padding-top: 9px;     /* adjust as needed */\n"
"    padding-left: 7px;    /* adjust as needed */\n"
"    padding-right: 50px;   /* adjust as needed */\n"
"    padding-bottom: 9px;\n"
"    color: #d9d9d9;\n"
"    background: transparent;\n"
"    border: none;\n"
"}\n"
"")
        self.writeJournal.setObjectName("writeJournal")

        self.sendButton_2 = QtWidgets.QPushButton(parent=self.journalsFrame)
        self.sendButton_2.setGeometry(QtCore.QRect(680, 313, 30, 30))
        self.sendButton_2.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Send Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Send Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Send Button/After.png);\n"
"}\n"
"")
        self.sendButton_2.setText("")
        self.sendButton_2.setObjectName("sendButton_2")
        self.sendButton_2.setToolTip("Send")
        self.sendButton_2.clicked.connect(self.save_journal_entry)


        self.backButton_2 = QtWidgets.QPushButton(parent=self.journalsFrame)
        self.backButton_2.setGeometry(QtCore.QRect(759, 207, 22, 106))
        self.backButton_2.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/After.png);\n"
"}\n"
"")
        self.backButton_2.setText("")
        self.backButton_2.setToolTip("Back")
        self.backButton_2.setObjectName("backButton_2")
        self.backButton_2.clicked.connect(self.showHomeScreenFrame)
        self.writeJournal.raise_()
        self.dateAndTimeFrame.raise_()
        self.sendButton_2.raise_()
        self.backButton_2.raise_()
        self.moodSupportFrame = QtWidgets.QFrame(parent=self.centralwidget)
        self.moodSupportFrame.setGeometry(QtCore.QRect(0, 0, 800, 520))
        self.moodSupportFrame.setStyleSheet("QFrame {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Frames/Mood Support);\n"
"}")
        self.moodSupportFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.moodSupportFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.moodSupportFrame.setObjectName("moodSupportFrame")
        self.backButton_3 = QtWidgets.QPushButton(parent=self.moodSupportFrame)
        self.backButton_3.setGeometry(QtCore.QRect(759, 207, 22, 106))
        self.backButton_3.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/After.png);\n"
"}\n"
"")
        self.backButton_3.setText("")
        self.backButton_3.setToolTip("Back")
        self.backButton_3.setObjectName("backButton_3")
        self.backButton_3.clicked.connect(self.showHomeScreenFrame)
        self.stressButton = QtWidgets.QPushButton(parent=self.moodSupportFrame)
        self.stressButton.setGeometry(QtCore.QRect(51, 144, 79, 79))
        self.stressButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Stress Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Stress Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Stress Button/After.png);\n"
"}")
        self.stressButton.setText("")
        self.stressButton.setObjectName("stressButton")
        self.stressButton.setToolTip("Stressed")
        self.stressButton.clicked.connect(self.onStressButtonClicked)

        self.sadButton = QtWidgets.QPushButton(parent=self.moodSupportFrame)
        self.sadButton.setGeometry(QtCore.QRect(198, 144, 79, 79))
        self.sadButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Sad Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Sad Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Sad Button/After.png);\n"
"}")
        self.sadButton.setText("")
        self.sadButton.setObjectName("sadButton")
        self.sadButton.setToolTip("Sad")
        self.sadButton.clicked.connect(self.onSadButtonClicked)

        self.lonelyButton = QtWidgets.QPushButton(parent=self.moodSupportFrame)
        self.lonelyButton.setGeometry(QtCore.QRect(343, 145, 79, 79))
        self.lonelyButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Lonely Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Lonely Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Lonely Button/After.png);\n"
"}")
        self.lonelyButton.setText("")
        self.lonelyButton.setObjectName("lonelyButton")
        self.lonelyButton.setToolTip("Lonely")
        self.lonelyButton.clicked.connect(self.onLonelyButtonClicked)

        self.angryButton = QtWidgets.QPushButton(parent=self.moodSupportFrame)
        self.angryButton.setGeometry(QtCore.QRect(489, 145, 79, 79))
        self.angryButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Angry Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Angry Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Angry Button/After.png);\n"
"}")
        self.angryButton.setText("")
        self.angryButton.setObjectName("angryButton")
        self.angryButton.setToolTip("Angry")
        self.angryButton.clicked.connect(self.onAngryButtonClicked)

        self.anxietyButton = QtWidgets.QPushButton(parent=self.moodSupportFrame)
        self.anxietyButton.setGeometry(QtCore.QRect(636, 145, 79, 79))
        self.anxietyButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Anxiety Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Anxiety Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Mood Support Emotions/Anxiety Button/After.png);\n"
"}")
        self.anxietyButton.setText("")
        self.anxietyButton.setObjectName("anxietyButton")
        self.anxietyButton.setToolTip("Anxious")
        self.anxietyButton.clicked.connect(self.onAnxietyButtonClicked)

        self.measuresFrame = QtWidgets.QFrame(parent=self.moodSupportFrame)
        self.measuresFrame.setGeometry(QtCore.QRect(50, 248, 664, 222))
        self.measuresFrame.setStyleSheet("QFrame {\n"
"    border-image: url(\"G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Dynamic/Mood Support/Measures.png\") 0 0 0 0 stretch stretch;\n"
"}\n"
"")
        self.measuresFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.measuresFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.measuresFrame.setObjectName("measuresFrame")
        self.measures = QtWidgets.QTextBrowser(parent=self.measuresFrame)
        self.measures.setGeometry(QtCore.QRect(0, 0, 664, 221))
        self.measures.setHtml("""
        <div style="text-align: center;">
                <div style="display: inline-block; vertical-align: middle; height: 221px; line-height: 100px;">
                <span style="font-family: Inter; font-weight: bold; font-size: 16px; color: #d9d9d9; line-height: normal; display: inline-block; vertical-align: middle;">
                        Please select an emotion above to view supportive suggestions.
                </span>
                </div>
        </div>
        """)


        self.measures.setStyleSheet("""
        QTextBrowser {
        font-family: "Inter";
        font-weight: bold;
        font-size: 14px;
        color: #d9d9d9;
        padding: 10px;
        background: transparent;
        border: none;
        }
        """)
        self.measures.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # optional: hide scrollbar if you want
        self.measures.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.measures.setReadOnly(True)
        self.measures.setObjectName("measures")

        self.stats1Frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.stats1Frame.setGeometry(QtCore.QRect(0, 0, 800, 520))
        self.stats1Frame.setStyleSheet("QFrame {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Frames/Stats);\n"
"}\n"
"")
        self.stats1Frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.stats1Frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.stats1Frame.setObjectName("stats1Frame")
        self.forwardButton = QtWidgets.QPushButton(parent=self.stats1Frame)
        self.forwardButton.setGeometry(QtCore.QRect(759, 207, 22, 106))
        self.forwardButton.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/After.png);\n"
"}\n"
"")
        self.forwardButton.setText("")
        self.forwardButton.setToolTip("Forward")
        self.forwardButton.setObjectName("forwardButton")
        self.forwardButton.clicked.connect(lambda: self.switch_frame(self.stats2Frame))

        self.stats2Frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.stats2Frame.setGeometry(QtCore.QRect(0, 0, 800, 520))
        self.stats2Frame.setStyleSheet("QFrame {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Frames/Stats1);\n"
"}")
        self.stats2Frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.stats2Frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.stats2Frame.setObjectName("stats2Frame")
        self.forwardButton_2 = QtWidgets.QPushButton(parent=self.stats2Frame)
        self.forwardButton_2.setGeometry(QtCore.QRect(759, 207, 22, 106))
        self.forwardButton_2.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/After.png);\n"
"}\n"
"")
        self.forwardButton_2.setText("")
        self.forwardButton_2.setToolTip("Forward")
        self.forwardButton_2.setObjectName("forwardButton_2")
        self.forwardButton_2.clicked.connect(lambda: self.switch_frame(self.stats3Frame))

        self.stats3Frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.stats3Frame.setGeometry(QtCore.QRect(0, 0, 800, 520))
        self.stats3Frame.setStyleSheet("QFrame {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Frames/Stats2);\n"
"}\n"
"")
        self.stats3Frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.stats3Frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.stats3Frame.setObjectName("stats3Frame")
        self.forwardButton_3 = QtWidgets.QPushButton(parent=self.stats3Frame)
        self.forwardButton_3.setGeometry(QtCore.QRect(759, 207, 22, 106))
        self.forwardButton_3.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/After.png);\n"
"}\n"
"")
        self.forwardButton_3.setText("")
        self.forwardButton_3.setToolTip("Forward")
        self.forwardButton_3.setObjectName("forwardButton_3")
        self.forwardButton_3.clicked.connect(lambda: self.switch_frame(self.stats4Frame))

        self.stats7Frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.stats7Frame.setGeometry(QtCore.QRect(0, 0, 800, 520))
        self.stats7Frame.setStyleSheet("QFrame {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Frames/Stats6);\n"
"}\n"
"")
        self.stats7Frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.stats7Frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.stats7Frame.setObjectName("stats7Frame")
        self.backButton_4 = QtWidgets.QPushButton(parent=self.stats7Frame)
        self.backButton_4.setGeometry(QtCore.QRect(759, 207, 22, 106))
        self.backButton_4.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Back Button/After.png);\n"
"}\n"
"")
        self.backButton_4.setText("")
        self.backButton_4.setToolTip("Back")
        self.backButton_4.setObjectName("backButton_4")
        self.backButton_4.clicked.connect(self.showHomeScreenFrame)

        self.stats4Frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.stats4Frame.setGeometry(QtCore.QRect(0, 0, 800, 520))
        self.stats4Frame.setStyleSheet("QFrame {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Frames/Stats3);\n"
"}\n"
"")
        self.stats4Frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.stats4Frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.stats4Frame.setObjectName("stats4Frame")
        self.forwardButton_4 = QtWidgets.QPushButton(parent=self.stats4Frame)
        self.forwardButton_4.setGeometry(QtCore.QRect(759, 207, 22, 106))
        self.forwardButton_4.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/After.png);\n"
"}\n"
"")
        self.forwardButton_4.setText("")
        self.forwardButton_4.setToolTip("Forward")
        self.forwardButton_4.setObjectName("forwardButton_4")
        self.forwardButton_4.clicked.connect(lambda: self.switch_frame(self.stats5Frame))

        self.stats5Frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.stats5Frame.setGeometry(QtCore.QRect(0, 0, 800, 520))
        self.stats5Frame.setStyleSheet("QFrame {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Frames/Stats4);\n"
"}\n"
"")
        self.stats5Frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.stats5Frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.stats5Frame.setObjectName("stats5Frame")
        self.forwardButton_5 = QtWidgets.QPushButton(parent=self.stats5Frame)
        self.forwardButton_5.setGeometry(QtCore.QRect(759, 207, 22, 106))
        self.forwardButton_5.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/After.png);\n"
"}\n"
"")
        self.forwardButton_5.setText("")
        self.forwardButton_5.setToolTip("Forward")
        self.forwardButton_5.setObjectName("forwardButton_5")
        self.forwardButton_5.clicked.connect(lambda: self.switch_frame(self.stats6Frame))

        self.stats6Frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.stats6Frame.setGeometry(QtCore.QRect(0, 0, 800, 520))
        self.stats6Frame.setStyleSheet("QFrame {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Frames/Stats5);\n"
"}\n"
"")
        self.stats6Frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.stats6Frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.stats6Frame.setObjectName("stats6Frame")
        self.forwardButton_6 = QtWidgets.QPushButton(parent=self.stats6Frame)
        self.forwardButton_6.setGeometry(QtCore.QRect(759, 207, 22, 106))
        self.forwardButton_6.setStyleSheet("QPushButton {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Before.png);\n"
"    background: transparent;\n"
"}\n"
"QPushButton:hover {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/Hover.png);\n"
"}\n"
"QPushButton:pressed {\n"
"    border-image: url(G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/Buttons/Forward Button/After.png);\n"
"}\n"
"")
        self.forwardButton_6.setText("")
        self.forwardButton_6.setToolTip("Forward")
        self.forwardButton_6.setObjectName("forwardButton_6")
        self.forwardButton_6.clicked.connect(lambda: self.switch_frame(self.stats7Frame))

        self.homeScreenFrame.raise_()
        self.chatbotFrame.raise_()
        self.journalsFrame.raise_()
        self.moodSupportFrame.raise_()
        self.stats1Frame.raise_()
        self.stats2Frame.raise_()
        self.stats3Frame.raise_()
        self.stats4Frame.raise_()
        self.stats5Frame.raise_()
        self.stats6Frame.raise_()
        self.stats7Frame.raise_()
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.closeButton.clicked.connect(MainWindow.close)
        self.chatbotFrame.hide()
        self.journalsFrame.hide()
        self.moodSupportFrame.hide()
        self.stats1Frame.hide()
        self.stats2Frame.hide()
        self.stats3Frame.hide()
        self.stats4Frame.hide()
        self.stats5Frame.hide()
        self.stats6Frame.hide()
        self.stats7Frame.hide()


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MindMate - Home"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("""
        QToolTip {
                color: #d9d9d9;
                border-radius: 6px;
                border: 1px solid #d9d9d9;
                padding: 2px;
                font-family: Inter;
                font-weight: bold;
                font-size: 14px;
                background-color: #383838;
                background-image: none;
                border-image: none;
        }
        """)

    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.setWindowFlags(MainWindow.windowFlags() & ~QtCore.Qt.WindowType.WindowMaximizeButtonHint)
    MainWindow.setFixedSize(MainWindow.size())
    MainWindow.setWindowIcon(QtGui.QIcon("G:/Users/MARS/Desktop/NTCC Aadi/In-House Project/MindMate/Assets/icon.png"))
    MainWindow.show()
    sys.exit(app.exec())

    