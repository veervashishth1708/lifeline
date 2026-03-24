const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');

const { decryptMidwayPayload } = require('./encryptionUtil');
const Telemetry = require('./models'); // Imports your easy-to-edit table structure!

const app = express();
app.use(cors());
app.use(express.json());

// ============================================
// 📊 CONNECT TO MONGODB (LOCAL DIRECTORY)
// ============================================
mongoose.connect('mongodb://127.0.0.1:27017/lifeline', {
    useNewUrlParser: true,
    useUnifiedTopology: true
}).then(() => {
    console.log("Connected to MongoDB database 'lifeline'");
}).catch((err) => {
    console.error("MongoDB Connection Error:", err.message);
    console.log("Make sure you have MongoDB Community Server installed and running!");
});

// 🌐 BACKEND API ROUTE
app.post('/api/secure_telemetry', async (req, res) => {
    const { src, midway_token } = req.body;

    if (!midway_token) {
        return res.status(400).json({ error: "Missing encrypted payload" });
    }

    // 1. Decrypt Master Key Payload
    const data = decryptMidwayPayload(midway_token);
    
    if (!data) {
        return res.status(403).json({ error: "Decryption Rejected" });
    }

    console.log(`\n📡 [Secure Telemetry] Decrypted Payload from ${src}:`, data);

    const lat = data.lat || null;
    const lng = data.lng || null;
    const pulse = data.pulse || 0;
    const sos = data.sos === 1;
    const rfid = data.rfid || null;

    // 2. Error Handling / Missing Data Resiliency
    if (pulse === 0 && !rfid && !sos) {
        console.warn("⚠️ Sensor Failure Detected (Pulse=0). No SOS triggered automatically by backend.");
    }

    // 3. Store Logs in MongoDB
    try {
        const newEntry = new Telemetry({
            src: src,
            lat: lat,
            lng: lng,
            pulse: pulse,
            sos: sos,
            rfid: rfid
        });

        await newEntry.save();
        console.log(`✅ Log saved to MongoDB. SOS Status: ${sos}`);
        
        // 4. Respond to Midway hardware (Triggers Midway RED LED if SOS)
        res.json({ success: true, sos_triggered: sos });
        
    } catch (err) {
        console.error("Database Write Error:", err.message);
        return res.status(500).json({ error: "Database failed" });
    }
});

// Start listening safely
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Lifeline Backend Node.js MongoDB Server listening on port ${PORT}`);
});
