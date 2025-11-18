 import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useChat } from "@/hooks/use-chat";
import { 
  ArrowRight, 
  Github, 
  Sun,
  Moon,
  Loader2
} from "lucide-react";

const EXAMPLE_PROMPTS = [
  "A login form with email/password validation and social sign-in buttons",
  "A product card with image, title, price, and add-to-cart button",
  "A settings toggle with smooth animation and theme integration",
  "A dashboard chart component with customizable data visualization"
];

const Index = () => {
  const [prompt, setPrompt] = useState("");
  const [isVisible, setIsVisible] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const navigate = useNavigate();
  
  // Initialize chat hook
  const { sendMessage, isLoading, error } = useChat();

  useEffect(() => {
    // Check system preference or saved preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    } else {
      // Default to light mode
      setIsDarkMode(false);
    }
  }, []);

  useEffect(() => {
    // Save theme preference
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim() || isLoading) return;
    
    try {
      console.log('Creating project from prompt:', prompt.trim());
      
      // Create project using new consolidated API
      const projectResponse = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_prompt: prompt.trim(),
          user_id: 1 // TODO: Get from Supabase auth
        })
      });
      
      if (!projectResponse.ok) {
        throw new Error('Failed to create project');
      }
      
      const projectData = await projectResponse.json();
      console.log('Project created:', projectData);
      
      // Require a valid project ID before redirecting
      if (!projectData?.project_id) {
        throw new Error('Project ID missing in response');
      }

      // Navigate to editor with project ID and initial prompt
      const editorUrl = `/editor?project=${projectData.project_id}&prompt=${encodeURIComponent(prompt.trim())}`;
      if (projectData.conversation_id) {
        navigate(`${editorUrl}&conversation=${projectData.conversation_id}`);
      } else {
        navigate(editorUrl);
      }
      
    } catch (err) {
      console.error('Failed to generate project:', err);
      // Do not redirect on error; show a simple alert
      const msg = err instanceof Error ? err.message : 'Failed to create project';
      window.alert(msg);
    }
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
            <br />
            
          </p>

          {/* Main Input */}
          <div className="max-w-2xl mx-auto mb-16">
            <div className="relative group">
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the Flutter widget you want..."
                className={`min-h-[140px] text-lg resize-none rounded-xl px-6 py-5 focus-visible:ring-1 placeholder:text-sm leading-relaxed transition-all ${
                  isDarkMode 
                    ? 'border border-white/20 bg-white/5 backdrop-blur-sm focus-visible:ring-white/30 focus-visible:border-white/40 text-white placeholder:text-gray-500' 
                    : 'border border-gray-300 bg-white backdrop-blur-sm focus-visible:ring-gray-400 focus-visible:border-gray-500 text-black placeholder:text-gray-400 shadow-sm'
                }`}
                disabled={isLoading}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    handleGenerate();
                  }
                }}
              />
              
              <div className="flex items-center justify-between mt-4">
                <div className={`text-sm flex items-center gap-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  {error && (
                    <span className="text-red-500 text-xs">
                      {error}
                    </span>
                  )}
                </div>
                
                <Button 
                  onClick={handleGenerate}
                  disabled={!prompt.trim() || isLoading}
                  className={`${isDarkMode ? 'bg-white text-black hover:bg-gray-200' : 'bg-black text-white hover:bg-gray-800'} px-6 py-2.5 rounded-lg font-medium transition-all`}
                >
                  {isLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                      Generating...
                    </>
                  ) : (
                    <>
                      Generate
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Example Prompts */}
          {!isLoading && (
            <div className="mb-24">
              <p className={`text-sm mb-6 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>Try these examples:</p>
              <div className="grid sm:grid-cols-2 gap-3 max-w-3xl mx-auto">
                {EXAMPLE_PROMPTS.map((example, index) => (
                  <button
                    key={index}
                    onClick={() => setPrompt(example)}
                    className={`text-left p-5 rounded-lg transition-all text-sm leading-relaxed group ${
                      isDarkMode 
                        ? 'border border-white/10 bg-white/5 backdrop-blur-sm hover:bg-white/10 hover:border-white/20' 
                        : 'border border-gray-200 bg-white backdrop-blur-sm hover:bg-gray-50 hover:border-gray-300 shadow-sm'
                    }`}
                  >
                    <span className={isDarkMode ? 'text-gray-300 group-hover:text-white' : 'text-gray-700 group-hover:text-black'}>{example}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

      </section>
    </div>
  );
};

export default Index;