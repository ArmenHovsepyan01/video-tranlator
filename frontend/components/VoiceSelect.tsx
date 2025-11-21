"use client"

import * as React from "react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {useEffect, useMemo, useState} from "react";
import {getVoiceLocales} from "@/lib/api";
import {Spinner} from "@/components/ui/spinner";

const LANGUAGE_NAMES: Record<string, string> = {
  en: "English",
  ru: "Русский",
  es: "Español",
  fr: "Français",
  de: "Deutsch",
  hy: "Հայերեն",
}

type VoiceLocale = {
    locale: string,
    voices: {
        gender: string,
        voice: string,
    }[]
}

interface IVoiceSelect {
    selectedVoice: string
    setSelectedVoice: React.Dispatch<React.SetStateAction<string>>
    setSelectedLanguage: React.Dispatch<React.SetStateAction<string>>
    selectedLanguage: string
}

export default function VoiceSelector({ selectedVoice, setSelectedLanguage, selectedLanguage, setSelectedVoice}: IVoiceSelect) {
  const [voicesData, setVoicesData] = useState<VoiceLocale[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const currentVoices = voicesData.find((item) => item.locale === selectedLanguage)?.voices || []

    useEffect(() => {
        (async () => {
            setIsLoading(true);
            try {
                const data = await getVoiceLocales();
                setVoicesData(data);
            } catch (error) {
                console.log(error);
            } finally {
                setIsLoading(false);
            }
        })()
    }, [setIsLoading, setVoicesData]);

  useEffect(() => {
    if (currentVoices.length > 0) {
      setSelectedVoice(currentVoices?.[0]?.voice)
    } else {
      setSelectedVoice("")
    }
  }, [selectedLanguage, currentVoices])

  const audioUrl = useMemo(() => `http://127.0.0.1:8000/samples/${selectedLanguage}/${selectedVoice}/sample.mp3`, [selectedLanguage, selectedVoice])

const audioRef = React.useRef<HTMLAudioElement>(null)

useEffect(() => {
    if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.load()
    }
}, [audioUrl]);

  if (isLoading) {
      return <Spinner className="w-full min-h-[60px]" />
  }

  return (
      <div className="space-y-6 w-full">
          <div className="space-y-2">
              <label className="text-sm font-medium">Language</label>
              <Select value={selectedLanguage} onValueChange={(val) => setSelectedLanguage(val)}>
                  <SelectTrigger className="w-full">
                      <SelectValue/>
                  </SelectTrigger>
                  <SelectContent>
                      {voicesData.map((item) => (
                          <SelectItem key={item.locale} value={item.locale}>
                              {LANGUAGE_NAMES[item.locale] || item.locale.toUpperCase()}
                          </SelectItem>
                      ))}
                  </SelectContent>
              </Select>
          </div>

          <div className="space-y-2">
              <label className="text-sm font-medium">Voice</label>
              <Select value={selectedVoice} onValueChange={setSelectedVoice} disabled={!selectedLanguage}>
                  <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select a voice..."/>
                  </SelectTrigger>
                  <SelectContent>
                      {currentVoices.map((v) => (
                          <SelectItem key={v.voice} value={v.voice}>
                              <span className="font-medium">{v.voice.split("-").pop()?.replace("Neural", "")}</span>
                              <span className="text-muted-foreground ml-2">({v.gender})</span>
                          </SelectItem>
                      ))}
                  </SelectContent>
              </Select>
          </div>

          <div className="text-sm text-muted-foreground pt-4 border-t">
              Selected: <strong>{selectedLanguage.toUpperCase()}</strong> →{" "}
              <strong>{selectedVoice || "none"}</strong>
          </div>

          <audio ref={audioRef} controls className="w-full">
              <source src={audioUrl} type="audio/mpeg" />
          </audio>
      </div>
  )
}