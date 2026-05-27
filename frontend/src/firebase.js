import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// TODO: Replace with your Firebase config
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "plantdoctor-tuaf.firebaseapp.com",
  projectId: "plantdoctor-tuaf",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
