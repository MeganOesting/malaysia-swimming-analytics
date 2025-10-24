import React from 'react';
import Link from 'next/link';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center py-4">
            <Link href="/" className="text-xl font-bold text-gray-800">
              Malaysia Swimming Analytics
            </Link>
            
            <div className="space-x-4">
              <Link href="/" className="text-gray-600 hover:text-gray-800">
                Home
              </Link>
              <Link href="/athletes" className="text-gray-600 hover:text-gray-800">
                Athletes
              </Link>
              <Link href="/meets" className="text-gray-600 hover:text-gray-800">
                Meets
              </Link>
              <Link href="/analytics" className="text-gray-600 hover:text-gray-800">
                Analytics
              </Link>
            </div>
          </div>
        </div>
      </nav>
      
      <main>
        {children}
      </main>
      
      <footer className="bg-gray-800 text-white py-8 mt-12">
        <div className="container mx-auto px-4 text-center">
          <p>&copy; 2025 Malaysia Swimming Analytics. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}


