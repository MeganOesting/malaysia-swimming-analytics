import type { AppProps } from 'next/app';
import '../frontend/styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}


