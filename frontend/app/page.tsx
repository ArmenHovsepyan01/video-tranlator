'use client';

import { useState, useRef } from 'react';
import Link from 'next/link'
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import VoiceSelector from '@/components/VoiceSelect';

import { uploadVideoWithProgress, ProgressEvent, CompleteEvent, ErrorEvent } from '@/lib/api';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [targetLanguage, setTargetLanguage] = useState<string>('en');
  const [selectedVoice, setSelectedVoice] = useState<string>("")
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompleteEvent | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setResult(null);
      setProgress(0);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a video file');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setResult(null);
    setProgress(0);
    setCurrentStage('');
    setMessage('Starting upload...');

    try {
      await uploadVideoWithProgress(
        file,
        targetLanguage,
        selectedVoice,
        (event: ProgressEvent) => {
          setProgress(event.progress);
          setCurrentStage(event.stage);
          setMessage(event.message);
        },
        (event: CompleteEvent) => {
          setProgress(100);
          setMessage('Processing complete!');
          setResult(event);
          setIsProcessing(false);
        },
        (event: ErrorEvent) => {
          setError(event.message);
          setIsProcessing(false);
          setProgress(0);
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      setIsProcessing(false);
      setProgress(0);
    }
  };

  const handleReset = () => {
    setFile(null);
    setProgress(0);
    setCurrentStage('');
    setMessage('');
    setError(null);
    setResult(null);
    setIsProcessing(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Video Translator
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Upload a video and translate it to your target language
          </p>
        </div>

        <Card className="w-full">
          <CardHeader>
            <CardTitle>Upload Video</CardTitle>
            <CardDescription>
              Select a video file and choose the target language for translation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="video-file">Video File</Label>
              <Input
                id="video-file"
                type="file"
                accept="video/*"
                onChange={handleFileChange}
                ref={fileInputRef}
                disabled={isProcessing}
                className="cursor-pointer"
              />
              {file && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>

            <VoiceSelector setSelectedVoice={setSelectedVoice} selectedLanguage={targetLanguage} selectedVoice={selectedVoice} setSelectedLanguage={setTargetLanguage} />

            {error && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
            )}

            {isProcessing && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">
                    {currentStage && currentStage.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className="text-gray-600 dark:text-gray-400">{progress}%</span>
                </div>
                <Progress value={progress} className="w-full" />
                {message && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">{message}</p>
                )}
              </div>
            )}

            {result && (
              <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
                <p className="text-sm font-medium text-green-800 dark:text-green-200 mb-2">
                  Video processed successfully!
                </p>
                <p className="text-xs text-green-700 dark:text-green-300">
                  Original language: {result.original_language}
                </p>
                <p className="text-xs text-green-700 dark:text-green-300">
                  Target language: {result.target_language}
                </p>
                <Link className="text-xs text-green-700 dark:text-green-300 mt-2" href={`http://127.0.0.1:8000/api/v1/video/download${result.translated_video}`}>
                  Output: {result.translated_video}
                </Link>
              </div>
            )}

            <div className="flex gap-4">
              <Button
                onClick={handleUpload}
                disabled={!file || isProcessing}
                className="flex-1"
              >
                {isProcessing ? 'Processing...' : 'Start Processing'}
              </Button>
              {(result || error) && (
                <Button
                  onClick={handleReset}
                  variant="outline"
                  disabled={isProcessing}
                >
                  Reset
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
