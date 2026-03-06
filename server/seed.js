import mongoose from 'mongoose';
import User from './models/User.js';
import dotenv from 'dotenv';

dotenv.config();

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/antigravity';

const users = [
    { userId: 'USR-001', name: 'Amit Verma' },
    { userId: 'USR-002', name: 'Priya Sharma' },
    { userId: 'USR-003', name: 'Rahul Khanna' },
    { userId: 'USR-004', name: 'Sonal Singh' },
    { userId: 'USR-005', name: 'Vikram Mehta' },
    { userId: 'USR-006', name: 'Anjali Gupta' },
    { userId: 'USR-007', name: 'Rohan Joshi' },
    { userId: 'USR-008', name: 'Mehak Kaur' },
    { userId: 'USR-009', name: 'Deepak Raj' },
    { userId: 'USR-010', name: 'Ishita Roy' }
];

const seedDB = async () => {
    try {
        await mongoose.connect(MONGODB_URI);
        console.log('Connected to MongoDB for seeding...');

        await User.deleteMany({});
        console.log('Old users cleared.');

        await User.insertMany(users);
        console.log('10 users seeded successfully!');

        mongoose.connection.close();
    } catch (err) {
        console.error('Seeding error:', err);
    }
};

seedDB();
