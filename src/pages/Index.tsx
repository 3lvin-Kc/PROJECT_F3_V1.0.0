import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { 
  ArrowRight, 
  Github, 
  Sun,
  Moon
} from "lucide-react";

const Index = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    } else {
      setIsDarkMode(false);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleStartBuilding = () => {
    navigate('/editor');
  };

  return (
    <div className={`min-h-screen relative ${isDarkMode ? 'bg-black' : 'bg-white'}`}>
      {/* Background pattern */}
      <div className={`absolute inset-0 ${isDarkMode ? 
        'bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)]' : 
        'bg-[linear-gradient(rgba(0,0,0,.08)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,.08)_1px,transparent_1px)]'} bg-[size:20px_20px] [mask-image:radial-gradient(ellipse_70%_50%_at_50%_0%,#000_70%,transparent_110%)]`} />
      
      {/* Header */}
      <header className={`relative z-10 border-b ${isDarkMode ? 'border-white/10 bg-black/80' : 'border-gray-200 bg-white/80'} backdrop-blur-sm sticky top-0`}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-3">
              <div className={`w-6 h-6 ${isDarkMode ? 'bg-white' : 'bg-black'} rounded-sm flex items-center justify-center`}>
                <span className={`text-xs font-bold ${isDarkMode ? 'text-black' : 'text-white'}`}>F3</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button 
              className={`flex items-center justify-center rounded-md text-sm font-medium transition-colors ${isDarkMode ? "text-gray-400 hover:text-white hover:bg-white/10 h-9 px-3" : "text-gray-600 hover:text-black hover:bg-gray-100 h-9 px-3"}`}
              onClick={() => setIsDarkMode(!isDarkMode)}
            >
              {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <button className={`flex items-center justify-center rounded-md text-sm font-medium transition-colors ${isDarkMode ? "text-gray-400 hover:text-white hover:bg-white/10 h-9 px-3" : "text-gray-600 hover:text-black hover:bg-gray-100 h-9 px-3"}`}>
              <Github className="w-4 h-4 mr-2" />
              GitHub
            </button>
            <button className={`flex items-center justify-center rounded-md text-sm font-medium transition-colors ${isDarkMode ? "text-gray-400 hover:text-white hover:bg-white/10 h-9 px-3" : "text-gray-600 hover:text-black hover:bg-gray-100 h-9 px-3"}`}>
              Docs
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 max-w-4xl mx-auto px-6 pt-32 pb-24">
        <div className={`text-center transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          
          {/* Status Badge */}
          <div className={`inline-flex items-center gap-2 ${isDarkMode ? 'bg-white/5 border border-white/10' : 'bg-gray-100 border border-gray-200'} px-3 py-1.5 rounded-full text-xs font-medium mb-8 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            <div className={`w-1.5 h-1.5 ${isDarkMode ? 'bg-green-400' : 'bg-green-500'} rounded-full`} />
            AI-powered Flutter widget generation
          </div>
          
          {/* Main Headline */}
          <h1 className="text-5xl md:text-3xl lg:text-5xl font-bold tracking-tighter mb-6 leading-none">
            <span className={isDarkMode ? "text-white" : "text-black"}>Fuck Flutter Flow </span>
          </h1>
          
          {/* Subtitle */}
          <p className={`text-xl md:text-2xl mb-12 max-w-2xl mx-auto leading-relaxed font-light ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Transform your ideas into production-ready Flutter widgets in seconds.
          </p>

          {/* Features Section */}
          <div className="max-w-3xl mx-auto mb-16">
            <div className="grid md:grid-cols-3 gap-8">
              <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-white/5 border border-white/10' : 'bg-gray-50 border border-gray-200'}`}>
                <div className={`text-2xl mb-3 ${isDarkMode ? 'text-white' : 'text-black'}`}>⚡</div>
                <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-black'}`}>Lightning Fast</h3>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Generate production-ready code in seconds</p>
              </div>
              <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-white/5 border border-white/10' : 'bg-gray-50 border border-gray-200'}`}>
                <div className={`text-2xl mb-3 ${isDarkMode ? 'text-white' : 'text-black'}`}>🎨</div>
                <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-black'}`}>Beautiful UI</h3>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Modern, responsive widgets ready to use</p>
              </div>
              <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-white/5 border border-white/10' : 'bg-gray-50 border border-gray-200'}`}>
                <div className={`text-2xl mb-3 ${isDarkMode ? 'text-white' : 'text-black'}`}>🤖</div>
                <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-black'}`}>AI-Powered</h3>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Intelligent code generation with context</p>
              </div>
            </div>
          </div>

          {/* CTA Button */}
          <Button 
            onClick={handleStartBuilding}
            className={`${isDarkMode ? 'bg-white text-black hover:bg-gray-200' : 'bg-black text-white hover:bg-gray-800'} px-8 py-3 rounded-lg font-medium transition-all text-lg`}
          >
            Start Building
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>

      </section>
    </div>
  );
};

export default Index;