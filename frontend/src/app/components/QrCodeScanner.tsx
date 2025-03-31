import React, { useEffect, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';

// For SSR compatibility
let Html5QrcodeLib: typeof Html5Qrcode | null = null;
if (typeof window !== 'undefined') {
  Html5QrcodeLib = Html5Qrcode;
}

interface QrCodeScannerProps {
  onScanSuccess: (decodedText: string) => void;
  onScanFailure?: (error: string) => void;
}

const QrCodeScanner: React.FC<QrCodeScannerProps> = ({
  onScanSuccess,
  onScanFailure,
}) => {
  const [scanner, setScanner] = useState<Html5Qrcode | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Clean up scanner when component unmounts
    return () => {
      if (scanner && isScanning) {
        scanner.stop().catch(error => console.error("Failed to stop scanner:", error));
      }
    };
  }, [scanner, isScanning]);

  const startScanner = async () => {
    try {
      setError(null);
      
      // Check if we're in a browser environment
      if (!Html5QrcodeLib) {
        setError("QR scanner is not available in this environment");
        return;
      }
      
      const html5QrCode = new Html5QrcodeLib("qr-reader");
      setScanner(html5QrCode);
      
      const qrCodeSuccessCallback = (decodedText: string) => {
        onScanSuccess(decodedText);
        stopScanner();
      };

      const qrCodeErrorCallback = (errorMessage: string) => {
        // This is called repeatedly, so we don't want to update state continuously
        console.log("QR Code scanning error:", errorMessage);
        if (onScanFailure) {
          onScanFailure(errorMessage);
        }
      };

      const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0,
      };

      await html5QrCode.start(
        { facingMode: "environment" },
        config,
        qrCodeSuccessCallback,
        qrCodeErrorCallback
      );
      
      setIsScanning(true);
    } catch (err) {
      setError("Could not start camera: " + (err instanceof Error ? err.message : String(err)));
      console.error("Error starting QR scanner:", err);
    }
  };

  const stopScanner = async () => {
    if (scanner && isScanning) {
      try {
        await scanner.stop();
        setIsScanning(false);
      } catch (error) {
        console.error("Failed to stop scanner:", error);
      }
    }
  };

  return (
    <div className="qr-scanner-container">
      <div id="qr-reader" style={{ width: '100%', maxWidth: '500px' }}></div>
      
      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}
      
      <div className="mt-4 flex space-x-4">
        {!isScanning ? (
          <button
            onClick={startScanner}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Start Camera
          </button>
        ) : (
          <button
            onClick={stopScanner}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Stop Camera
          </button>
        )}
      </div>
    </div>
  );
};

export default QrCodeScanner;