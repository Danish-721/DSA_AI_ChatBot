import { GoogleGenerativeAI } from "https://esm.run/@google/generative-ai";

const apiKey = "AIzaSyBnkn34d9fim6hAtaWLW3HcrhEA_jpT54k"; 

const systemInstruction = `
Tum ek 'DSA Dost' ho. Ek expert Data Structures aur Algorithms (DSA) teacher, jo bilkul dost ki tarah samjhaata hai.previous reply ko save kar lena history me. Previous sari conversation ko yaad bhi rakhna kyuki user jyada type nhi karta.
    
Tumhare Rules:

1. **Definition:** Har topic jo bhi pucha h uski definition provide karo english or technical language me jo ki user exam me bhi likh sake. English or hindi language ke alava koi or language use mat karna. 

2.  **Ekdum Simple Rakho:** Har topic ko itna aasan bana do jaise koi kahani suna rahe ho. Real-life example do, jaise Stack ko 'shaadi ki plates ka dher' bolkar samjhana.

3.  **Har Baar Naya Answer (Sabse Zaroori):** Ye tumhara sabse important rule hai. Agar user ek hi sawaal baar baar puche, to har baar tumhara samjhaane ka tareeka bilkul naya aur alag hona chahiye. Nayi analogy, naya real-world example, kuch bhi use karo par answer copy-paste mat karna. User ko hamesha kuch naya milna chahiye.

4.  **Do Step Mein Samjhao:**
    -   Pehle, sirf concept ko chote aur aasan shabdo mein batao.
    -   Uske baad, user se pucho ki "Example chahiye kya?" ya "Code dekhna hai iska?". Par ye jyada baar nhi puchne, user jab coding ka question kare tab hi puchna.

5. **code and example:** agar user code and example mange to use code and exaxmple bhi provide karo.

6.  **Dost Jaisa Tone:** Tumhara andaaz ekdam friendly aur encouraging hona chahiye. "Mast sawaal hai!", "Chalo, isko phaadte hain!" jaise phrases use karo. User ko lagna chahiye ki wo apne dost se sikh raha hai.

7.  **Faltu Sawaal?:** Agar koi DSA ya programming ke alawa kuch aur puche (jaise 'film ka hero kaun hai?is type ke koi bhi sawal ho skte h'), to gusse mein nahi, pyaar se mana karo. Bolo, "Yaar, ye to mere topic se bahar hai! Main to DSA ka expert hoon. Chalo DSA ka koi sawaal pucho! har baar baar alag reply karna"

8.  **GeeksforGeeks ka Reference:** Zaroorat padne par, user ko GeeksforGeeks ke baare mein bata sakte ho. Jaise, "Aur detail mein jaana hai to GeeksforGeeks check karlo, wahan mast examples milenge.
9.  **Out of the box:** Agar user esa question puch le jo tumhe nhi pata to use reply karna "Example Me abhi beta version hu. I am under development."
`;

const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatBox = document.getElementById('chat-box');
const sendBtn = document.getElementById('send-btn');

const genAI = new GoogleGenerativeAI(apiKey);
const model = genAI.getGenerativeModel({
    model: "gemini-2.0-flash",
    systemInstruction: systemInstruction,
});

const history = [];

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const userMessage = userInput.value.trim();
    if (!userMessage) return;

    addMessageToChatBox(userMessage, 'user-message');
    userInput.value = '';
    sendBtn.disabled = true;

    const typingIndicator = addTypingIndicator();

    try {
        history.push({
            role: "user",
            parts: [{ text: userMessage }]
        });
        
        const chat = model.startChat({
            history: history,
            generationConfig: {
                maxOutputTokens: 500,
            },
        });
        
        const result = await chat.sendMessage(userMessage);
        const response = await result.response;
        const botMessage = response.text();

        history.push({
            role: "model",
            parts: [{ text: botMessage }]
        });

        chatBox.removeChild(typingIndicator);
        addMessageToChatBox(botMessage, 'bot-message');

    } catch (error) {
        chatBox.removeChild(typingIndicator);
        addMessageToChatBox("Oops! Kuch gadbad ho gayi. Kripya thodi der baad try karein.", 'bot-message');
        console.error("AI Error:", error);
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
});

function addMessageToChatBox(text, className) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${className}`;

    let formattedText = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');

    const p = document.createElement('p');
    p.innerHTML = formattedText;
    messageDiv.appendChild(p);

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addTypingIndicator() {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'message bot-message typing-indicator';
    indicatorDiv.innerHTML = `<span></span><span></span><span></span>`;
    chatBox.appendChild(indicatorDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    return indicatorDiv;
}

document.getElementById('download-btn').addEventListener('click', () => {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ unit: "mm", format: "a4" });

    const messages = document.querySelectorAll('#chat-box .message');
    let y = 20;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(12);

    messages.forEach(msg => {
        let prefix = msg.classList.contains('user-message') ? "You: " : "Bot: ";
        let text = msg.innerText.trim();

        doc.setFont("helvetica", "bold");
        doc.setTextColor(0, 102, 204); 
        doc.text(prefix, 10, y);

        doc.setFont("helvetica", "normal");
        doc.setTextColor(0, 0, 0); 
        let splitText = doc.splitTextToSize(text, 180);

        doc.text(splitText, 10, y + 7);

        y += (splitText.length * 7) + 10;

        if (y > 270) {
            doc.addPage();
            y = 20;
        }
    });

    doc.save('dsa-chat.pdf');
});

