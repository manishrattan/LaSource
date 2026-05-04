import { useState, useEffect } from 'react';
import {
  FolderOpen,
  FileCode,
  ShieldAlert,
  Server,
  Cloud,
  ChevronRight,
  Terminal,
  FileText,
  Activity,
  ShieldCheck,
  Ban,
  Fingerprint
} from 'lucide-react';

// Import the generated files as raw strings using Vite's ?raw feature
import readmeMd from '../README.md?raw';
import specMd from '../SPEC.md?raw';
import openapiYaml from '../openapi.yaml?raw';
import githubActions from '../.github/workflows/azure-tier3-ci-cd.yml?raw';

// Clean Architecture Files
import factoryPy from '../src/lavoie/infrastructure/factory.py?raw';
import configPy from '../src/lavoie/infrastructure/config.py?raw';
import mainPy from '../src/lavoie/application/main.py?raw';
import shieldPy from '../src/lavoie/application/middleware/shield.py?raw';
import scrubberPy from '../src/lavoie/domain/services/scrubber.py?raw';
import providerPy from '../src/lavoie/domain/interfaces/provider.py?raw';
import openaiBicep from '../infra/modules/openai.bicep?raw';

import testShieldPy from '../tests/test_shield.py?raw';
import testInitPy from '../tests/__init__.py?raw';
import MOCK_EVENTS from './mockData.json';

const FILE_STRUCTURE: any[] = [
  {
    name: '.github',
    type: 'folder',
    icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
    children: [
      {
        name: 'workflows',
        type: 'folder',
        icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
        children: [
          { name: 'azure-tier3-ci-cd.yml', type: 'file', content: githubActions, icon: <FileCode className="w-4 h-4 text-amber-400" /> },
        ]
      }
    ],
  },
  {
    name: 'README.md',
    type: 'file',
    content: readmeMd,
    icon: <FileText className="w-4 h-4 text-blue-300" />,
  },
  {
    name: 'SPEC.md',
    type: 'file',
    content: specMd,
    icon: <FileText className="w-4 h-4 text-purple-300" />,
  },
  {
    name: 'openapi.yaml',
    type: 'file',
    content: openapiYaml,
    icon: <FileCode className="w-4 h-4 text-green-300" />,
  },
  {
    name: 'infra',
    type: 'folder',
    icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
    children: [
      { 
        name: 'modules', 
        type: 'folder',
        icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
        children: [
          { name: 'openai.bicep', type: 'file', content: openaiBicep, icon: <Cloud className="w-4 h-4 text-sky-400" /> },
        ]
      }
    ],
  },
  {
    name: 'src',
    type: 'folder',
    icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
    children: [
      {
        name: 'lavoie',
        type: 'folder',
        icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
        children: [
          {
            name: 'application',
            type: 'folder',
            icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
            children: [
              {
                name: 'middleware',
                type: 'folder',
                icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
                children: [
                  { name: 'main.py', type: 'file', content: mainPy, icon: <FileCode className="w-4 h-4 text-emerald-400" /> },
                  { name: 'shield.py', type: 'file', content: shieldPy, icon: <ShieldAlert className="w-4 h-4 text-red-500" /> },
                ]
              }
            ]
          },
          {
            name: 'domain',
            type: 'folder',
            icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
            children: [
              {
                name: 'interfaces',
                type: 'folder',
                icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
                children: [
                  { name: 'provider.py', type: 'file', content: providerPy, icon: <FileCode className="w-4 h-4 text-blue-400" /> },
                ]
              },
              {
                name: 'services',
                type: 'folder',
                icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
                children: [
                  { name: 'scrubber.py', type: 'file', content: scrubberPy, icon: <ShieldCheck className="w-4 h-4 text-emerald-400" /> },
                ]
              }
            ]
          },
          {
            name: 'infrastructure',
            type: 'folder',
            icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
            children: [
              { name: 'config.py', type: 'file', content: configPy, icon: <FileCode className="w-4 h-4 text-orange-400" /> },
              { name: 'factory.py', type: 'file', content: factoryPy, icon: <FileCode className="w-4 h-4 text-orange-400" /> },
            ]
          }
        ]
      }
    ]
  },
  {
    name: 'tests',
    type: 'folder',
    icon: <FolderOpen className="w-4 h-4 text-emerald-500" />,
    children: [
      { name: '__init__.py', type: 'file', content: testInitPy },
      { name: 'test_shield.py', type: 'file', content: testShieldPy, icon: <FileCode className="w-4 h-4 text-blue-400" /> },
    ],
  },
];

export default function App() {
  const [activeFile, setActiveFile] = useState<any>(FILE_STRUCTURE[5].children[0].children[0].children[0].children[1]); // shield.py default
  const [viewMode, setViewMode] = useState<'explorer' | 'dashboard'>('dashboard');
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({
    '.github': true,
    'workflows': true,
    'infra': true,
    'modules': true,
    'src': true,
    'lavoie': true,
    'application': true,
    'middleware': true,
    'domain': false,
    'infrastructure': false,
    'tests': false,
  });

  const [streamedEvents, setStreamedEvents] = useState<any[]>(MOCK_EVENTS.slice(0, 3));

  useEffect(() => {
    if (viewMode === 'dashboard') {
      const interval = setInterval(() => {
        setStreamedEvents(current => {
          if (current.length >= MOCK_EVENTS.length) return current; // stop adding after we hit the max mock events
          return [...current, MOCK_EVENTS[current.length]];
        });
      }, 3500);
      return () => clearInterval(interval);
    }
  }, [viewMode]);

  const toggleFolder = (name: string) => {
    setExpandedFolders((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const renderFileTree = (nodes: any[], depth = 0) => {
    return nodes.map((item) => (
      <div key={item.name} className="mb-[2px]">
        {item.type === 'folder' ? (
          <>
            <button
              onClick={() => toggleFolder(item.name)}
              className="flex items-center w-full px-2 py-1.5 text-sm rounded hover:bg-[#21262d] transition-colors"
              style={{ paddingLeft: `${depth * 12 + 8}px` }}
            >
              <ChevronRight
                className={`w-3 h-3 mr-1.5 transition-transform ${
                  expandedFolders[item.name] ? 'rotate-90' : ''
                }`}
              />
              {item.icon}
              <span className="ml-2">{item.name}</span>
            </button>
            {expandedFolders[item.name] && (
              <div className="border-l border-[#30363d] ml-[10px] mt-1 space-y-[2px]">
                {renderFileTree(item.children, depth + 1)}
              </div>
            )}
          </>
        ) : (
          <button
            onClick={() => setActiveFile(item)}
            className={`flex items-center w-full py-1.5 text-sm rounded transition-colors ${
              activeFile.name === item.name
                ? 'bg-blue-500/10 text-blue-400'
                : 'hover:bg-[#21262d] text-[#8b949e] hover:text-[#c9d1d9]'
            }`}
            style={{ paddingLeft: `${depth * 12 + 28}px` }}
          >
            {item.icon || <FileCode className="w-3.5 h-3.5 text-[#8b949e]" />}
            <span className="ml-2 font-mono text-xs">{item.name}</span>
          </button>
        )}
      </div>
    ));
  };

  return (
    <div className="flex h-screen bg-[#0d1117] text-[#c9d1d9] font-sans antialiased selection:bg-blue-500/30">
      {/* Sidebar */}
      <div className="w-72 flex-shrink-0 border-r border-[#30363d] bg-[#161b22] flex flex-col">
        <div className="p-4 border-b border-[#30363d] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-6 h-6 text-emerald-500" />
            <h1 className="font-bold text-lg text-white tracking-tight">LaSource</h1>
          </div>
        </div>
        
        {/* Navigation Modes */}
        <div className="px-3 pt-4 pb-2 space-y-1 border-b border-[#30363d] pb-4">
          <button 
            onClick={() => setViewMode('explorer')}
            className={`flex items-center w-full px-3 py-2 text-sm font-medium rounded-md ${viewMode === 'explorer' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'text-[#8b949e] hover:bg-[#21262d] hover:text-[#c9d1d9]'}`}
          >
            <FolderOpen className="w-4 h-4 mr-2" />
            Code Explorer
          </button>
          <button 
            onClick={() => setViewMode('dashboard')}
            className={`flex items-center w-full px-3 py-2 text-sm font-medium rounded-md ${viewMode === 'dashboard' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-[#8b949e] hover:bg-[#21262d] hover:text-[#c9d1d9]'}`}
          >
            <Activity className="w-4 h-4 mr-2" />
            Audit Dashboard
          </button>
        </div>

        {viewMode === 'explorer' && (
          <div className="overflow-y-auto flex-1 p-2 space-y-1">
            <div className="text-sm font-medium px-2 py-1 flex items-center text-[#8b949e] uppercase tracking-widest mt-2 mb-1">
              Project Structure
            </div>
            
            <div className="pl-2">
              {renderFileTree(FILE_STRUCTURE)}
            </div>
          </div>
        )}
        
        {viewMode === 'dashboard' && (
          <div className="p-4 space-y-4">
            <div className="text-xs font-semibold text-[#8b949e] uppercase tracking-widest">
              Live Protection Status
            </div>
            <div className="bg-[#21262d] p-3 rounded-lg border border-[#30363d]">
               <div className="flex items-center justify-between">
                 <span className="text-emerald-400 text-sm font-medium">Gateway Active</span>
                 <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
               </div>
               <p className="text-xs text-[#8b949e] mt-1">Intercepting outbound AI Provider traffic.</p>
            </div>
            <div className="bg-[#21262d] p-3 rounded-lg border border-[#30363d] space-y-2">
               <div className="flex items-center text-xs text-[#8b949e]">
                 <Fingerprint className="w-3.5 h-3.5 mr-2 text-blue-400" /> Entra ID Validated
               </div>
               <div className="flex items-center text-xs text-[#8b949e]">
                 <ShieldCheck className="w-3.5 h-3.5 mr-2 text-purple-400" /> PII Scrubber Active
               </div>
               <div className="flex items-center text-xs text-[#8b949e]">
                 <Ban className="w-3.5 h-3.5 mr-2 text-red-400" /> IP Rate Limited
               </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#0d1117] h-screen overflow-hidden">
        {viewMode === 'explorer' ? (
          <>
            <div className="flex bg-[#161b22] border-b border-[#30363d] overflow-x-auto min-h-[40px] shrink-0">
              <div className="flex items-center px-4 py-2 border-r border-[#30363d] bg-[#0d1117] border-t-2 border-t-blue-500">
                {activeFile.icon || <FileCode className="w-4 h-4 text-gray-400" />}
                <span className="ml-2 text-sm font-medium font-mono">{activeFile.name}</span>
              </div>
            </div>

            <div className="px-4 py-3 border-b border-[#30363d] flex items-center justify-between text-xs text-[#8b949e] bg-[#0d1117] shrink-0">
              <div className="flex items-center space-x-2">
                <span className="bg-[#21262d] px-2 py-1 rounded text-white font-mono flex items-center">
                  <Terminal className="w-3 h-3 mr-2 text-blue-400" />
                  Azure Tier 3 Compliant Proxy
                </span>
                <span>OpenTelemetry Ready</span>
              </div>
              <div className="font-mono">{activeFile.content.split('\\n').length} lines</div>
            </div>

            <div className="flex-1 overflow-auto p-4 bg-[#0d1117]">
              <pre className="font-mono text-[13px] leading-6 text-[#e6edf3]">
                <code>{activeFile.content}</code>
              </pre>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col p-8 overflow-y-auto w-full max-w-5xl mx-auto">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-2">Live Audit Dashboard</h2>
              <p className="text-[#8b949e]">Monitor intercepted requests flowing through the LaSource Shield to upstream AI providers.</p>
            </div>

            <div className="grid grid-cols-3 gap-6 mb-8">
              <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm">
                <div className="text-[#8b949e] text-sm font-medium mb-1 flex justify-between items-center">
                  Requests Processed
                  <Server className="w-4 h-4 text-emerald-500" />
                </div>
                <div className="text-3xl font-bold text-white tracking-tight">8,241</div>
                <div className="text-xs text-emerald-400 mt-2 font-medium">+142 this hour</div>
              </div>
              <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-sm">
                <div className="text-[#8b949e] text-sm font-medium mb-1 flex justify-between items-center">
                  PII Events Prevented
                  <ShieldCheck className="w-4 h-4 text-blue-400" />
                </div>
                <div className="text-3xl font-bold text-white tracking-tight">342</div>
                <div className="text-xs text-emerald-400 mt-2 font-medium">100% Redaction Success</div>
              </div>
              <div className="bg-[#161b22] border border-red-900/30 rounded-xl p-5 shadow-sm relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/5 rounded-full blur-3xl -mr-16 -mt-16"></div>
                <div className="text-[#8b949e] text-sm font-medium mb-1 flex justify-between items-center relative">
                  Policy Interventions
                  <Ban className="w-4 h-4 text-red-500" />
                </div>
                <div className="text-3xl font-bold text-white tracking-tight relative">14</div>
                <div className="text-xs text-red-400 mt-2 font-medium relative">Strict Keyword Deny</div>
              </div>
            </div>

            <div className="bg-[#161b22] border border-[#30363d] rounded-xl flex-1 flex flex-col min-h-[400px]">
              <div className="px-5 py-4 border-b border-[#30363d] flex justify-between items-center bg-[#0d1117] rounded-t-xl">
                <h3 className="font-semibold text-white">Stream: LaSource Audit Log</h3>
                <div className="flex items-center space-x-2 text-xs">
                  <span className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  <span className="text-[#8b949e] font-mono">Real-time trace</span>
                </div>
              </div>
              <div className="p-0 overflow-y-auto flex-1">
                <table className="w-full text-left text-sm">
                  <thead className="bg-[#21262d]/50 text-[#8b949e] text-xs uppercase font-semibold border-b border-[#30363d]">
                    <tr>
                      <th className="px-5 py-3">Timestamp</th>
                      <th className="px-5 py-3">Correlation ID</th>
                      <th className="px-5 py-3">Action</th>
                      <th className="px-5 py-3">Trace Detail</th>
                    </tr>
                  </thead>
                  <tbody className="font-mono text-[13px]">
                    {streamedEvents.map((evt, idx) => (
                      <tr key={idx} className="border-b border-[#30363d]/50 hover:bg-[#21262d]/30 transition-colors">
                        <td className="px-5 py-3 text-[#8b949e] whitespace-nowrap">{evt.time}</td>
                        <td className="px-5 py-3 text-[#8b949e] whitespace-nowrap">{evt.id}</td>
                        <td className="px-5 py-3">
                           <span className={`px-2 py-1 rounded text-xs font-bold ${
                             evt.action === 'PASS' ? 'text-emerald-400 bg-emerald-500/10' : 
                             evt.action === 'REDACT' ? 'text-amber-400 bg-amber-500/10' : 
                             'text-red-400 bg-red-500/10'
                           }`}>
                             {evt.action}
                           </span>
                        </td>
                        <td className="px-5 py-3 text-white">
                          <div className={`${evt.action === 'REDACT' ? 'opacity-80' : ''}`}>
                            {evt.detail}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
