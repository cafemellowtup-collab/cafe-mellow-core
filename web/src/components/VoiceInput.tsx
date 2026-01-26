"use client";

import { useState, useEffect, useRef } from "react";
import { Mic, MicOff, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  onStart?: () => void;
  onEnd?: () => void;
  language?: string;
}

export default function VoiceInput({ 
  onTranscript, 
  onStart, 
  onEnd,
  language = "en-IN" 
}: VoiceInputProps) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  
  useEffect(() => {
    // Check if Web Speech API is supported
    if (typeof window !== "undefined") {
      const SpeechRecognition = 
        (window as any).SpeechRecognition || 
        (window as any).webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        setIsSupported(true);
        
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = language;
        
        recognition.onstart = () => {
          setIsListening(true);
          onStart?.();
        };
        
        recognition.onresult = (event: SpeechRecognitionEvent) => {
          let interim = "";
          let final = "";
          
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            if (result.isFinal) {
              final += result[0].transcript;
            } else {
              interim += result[0].transcript;
            }
          }
          
          if (final) {
            setTranscript(prev => prev + " " + final);
            onTranscript(final.trim());
          }
          
          setInterimTranscript(interim);
        };
        
        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
          console.error("Speech recognition error:", event.error);
          setIsListening(false);
        };
        
        recognition.onend = () => {
          setIsListening(false);
          setInterimTranscript("");
          onEnd?.();
        };
        
        recognitionRef.current = recognition;
      }
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [language, onStart, onEnd, onTranscript]);
  
  const toggleListening = () => {
    if (!recognitionRef.current) return;
    
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setTranscript("");
      setInterimTranscript("");
      recognitionRef.current.start();
      setIsListening(true);
    }
  };
  
  if (!isSupported) {
    return null; // Hide if not supported
  }
  
  return (
    <div className="relative">
      <motion.button
        whileTap={{ scale: 0.95 }}
        onClick={toggleListening}
        className={`relative rounded-full p-3 transition ${
          isListening
            ? "bg-red-500 text-white shadow-lg shadow-red-500/30"
            : "bg-white/10 text-zinc-300 hover:bg-white/20"
        }`}
        title={isListening ? "Stop recording" : "Start voice input"}
      >
        {isListening ? <MicOff size={18} /> : <Mic size={18} />}
        
        {isListening && (
          <motion.span
            className="absolute -inset-1 rounded-full border-2 border-red-500"
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.5, 0, 0.5],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        )}
      </motion.button>
      
      <AnimatePresence>
        {(isListening && (transcript || interimTranscript)) && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute bottom-full right-0 mb-2 max-w-xs rounded-xl border border-white/10 bg-black/90 px-3 py-2 text-xs text-zinc-200 backdrop-blur-xl"
          >
            <div className="flex items-center gap-2">
              <Loader2 size={12} className="animate-spin text-red-400" />
              <span className="text-zinc-400">Listening...</span>
            </div>
            {transcript && (
              <div className="mt-1 font-medium">{transcript}</div>
            )}
            {interimTranscript && (
              <div className="mt-1 italic text-zinc-400">{interimTranscript}</div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
