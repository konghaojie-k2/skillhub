# Frontend Extension Patterns

How to extend Agent Chat UI with custom pages and components.

## Two Extension Approaches

### Approach A: Original Thread Component (Minimal Changes)

Keep the original Agent Chat UI chat interface with minimal modifications.

**Use when:** Chat-first application, minimal customization needed

**Implementation:**

```typescript
// src/app/page.tsx
"use client";

import { Thread } from "@/components/thread";

export default function HomePage() {
  return (
    <div className="h-screen">
      {/* Original Thread component - full chat UI */}
      <Thread />
    </div>
  );
}
```

**Pros:**
- Zero setup, works out of the box
- Full chat features (history, artifacts, streaming)
- No state management needed

**Cons:**
- Limited customization
- Can't easily add custom UI elements

---

### Approach B: Custom UI with useStream Hook (Full Control)

Build custom interfaces using LangGraph SDK's `useStream` hook.

**Use when:** Business-specific interfaces, custom workflows

**Implementation:**

```typescript
// src/app/custom/page.tsx
"use client";

import { useState } from "react";
import { useStream } from "@langchain/langgraph-sdk/react";

export default function CustomPage() {
  const [input, setInput] = useState("");

  // Use LangGraph SDK for agent connection
  const { submitMessage, messages } = useStream({
    apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:2024",
    assistantId: process.env.NEXT_PUBLIC_ASSISTANT_ID || "your_agent",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    submitMessage({ content: input });
    setInput("");
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      {/* Custom UI - your design */}
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Custom Agent Interface</h1>

        {/* Messages */}
        <div className="bg-white rounded-lg shadow p-6 mb-6 max-h-96 overflow-y-auto">
          {messages.map((msg, i) => (
            <div key={i} className={`mb-4 ${msg.role === "user" ? "text-right" : "text-left"}`}>
              <div className={`inline-block px-4 py-2 rounded-lg ${
                msg.role === "user" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-900"
              }`}>
                {typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content)}
              </div>
            </div>
          ))}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            发送
          </button>
        </form>
      </div>
    </div>
  );
}
```

**Pros:**
- Full UI/UX control
- Integrate with business logic
- Custom state management
- Add multiple pages/routes

**Cons:**
- More code to maintain
- Need to implement chat features manually

---

## Hybrid Approach (Recommended)

Use both: keep `/page.tsx` for chat, add custom pages for business features:

```
src/app/
├── page.tsx              # Original Thread (chat interface)
├── dashboard/
│   └── page.tsx          # Custom dashboard with useStream
├── analysis/
│   └── page.tsx          # Analysis results page
└── dataset/
    └── page.tsx          # Dataset management
```

## Common UI Patterns

### Pattern 1: Chat + Side Panel

```typescript
export default function ChatWithSidePanel() {
  const [selectedItem, setSelectedItem] = useState(null);

  return (
    <div className="flex h-screen">
      {/* Left: Chat */}
      <div className="flex-1">
        <Thread />
      </div>

      {/* Right: Side Panel */}
      {selectedItem && (
        <div className="w-96 bg-white border-l">
          <h2>Details</h2>
          {/* Custom content */}
        </div>
      )}
    </div>
  );
}
```

### Pattern 2: Tabbed Interface

```typescript
export default function TabbedInterface() {
  const [activeTab, setActiveTab] = useState("chat");

  return (
    <div>
      {/* Tabs */}
      <nav className="flex border-b">
        <button onClick={() => setActiveTab("chat")}>Chat</button>
        <button onClick={() => setActiveTab("browse")}>Browse</button>
        <button onClick={() => setActiveTab("upload")}>Upload</button>
      </nav>

      {/* Content */}
      {activeTab === "chat" && <Thread />}
      {activeTab === "browse" && <BrowsePage />}
      {activeTab === "upload" && <UploadPage />}
    </div>
  );
}
```

### Pattern 3: Modal/Dialog for Results

```typescript
export default function ResultsModal() {
  const [showResult, setShowResult] = useState(false);
  const [resultData, setResultData] = useState(null);

  const handleItemClick = async (item) => {
    const data = await fetchDetails(item.id);
    setResultData(data);
    setShowResult(true);
  };

  return (
    <div>
      {/* Main content */}
      <ItemList onItemClick={handleItemClick} />

      {/* Modal overlay */}
      {showResult && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center">
          <div className="bg-white rounded-xl p-8 max-w-2xl">
            <h2>Results</h2>
            {resultData && <ResultDisplay data={resultData} />}
            <button onClick={() => setShowResult(false)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
```

## API Integration Patterns

### FastAPI Business Endpoints

```typescript
// src/lib/api.ts
const FASTAPI_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';

export const businessAPI = {
  // Dataset operations
  listDatasets: async () => {
    const response = await fetch(`${FASTAPI_URL}/api/v1/datasets`);
    return response.json();
  },

  uploadDataset: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${FASTAPI_URL}/api/v1/datasets/upload`, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  },

  // Analysis results
  getAnalysisResults: async (datasetId: string) => {
    const response = await fetch(`${FASTAPI_URL}/api/v1/datasets/${datasetId}/analysis-results`);
    return response.json();
  },

  // Agent query
  queryAgent: async (query: string) => {
    const response = await fetch(`${FASTAPI_URL}/api/agents/query_agent/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    return response.json();
  },
};
```

### Usage in Components

```typescript
import { businessAPI } from '@/lib/api';
import { useState, useEffect } from 'react';

export function DatasetList() {
  const [datasets, setDatasets] = useState([]);

  useEffect(() => {
    businessAPI.listDatasets().then(setDatasets);
  }, []);

  const handleUpload = async (file: File) => {
    const result = await businessAPI.uploadDataset(file);
    setDatasets(prev => [...prev, result.dataset]);
  };

  return (
    <div>
      {datasets.map(ds => (
        <div key={ds.id}>{ds.name}</div>
      ))}
      <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />
    </div>
  );
}
```

## Streaming Progress (SSE)

For real-time progress updates:

```typescript
export function useAnalysisProgress(analysisId: string) {
  const [progress, setProgress] = useState({
    stage: "",
    percentage: 0,
    message: ""
  });

  useEffect(() => {
    const eventSource = new EventSource(
      `http://localhost:8000/api/analysis/${analysisId}/progress`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);
    };

    return () => eventSource.close();
  }, [analysisId]);

  return progress;
}
```

## Agent Switching

### Static Agent (Environment Variable)

```typescript
// .env.local
NEXT_PUBLIC_ASSISTANT_ID=agent_a

// component.tsx
const { submitMessage } = useStream({
  assistantId: process.env.NEXT_PUBLIC_ASSISTANT_ID, // Fixed
});
```

### Dynamic Agent Selection

```typescript
export function AgentSelector() {
  const [currentAgent, setCurrentAgent] = useState("agent_a");

  const { submitMessage, messages } = useStream({
    apiUrl: "http://localhost:2024",
    assistantId: currentAgent, // Changes with state
  });

  return (
    <div>
      <select value={currentAgent} onChange={(e) => setCurrentAgent(e.target.value)}>
        <option value="agent_a">Agent A (Chat)</option>
        <option value="agent_b">Agent B (Analysis)</option>
        <option value="agent_c">Agent C (Query)</option>
      </select>

      <MessageList messages={messages} />
      <MessageInput onSubmit={submitMessage} />
    </div>
  );
}
```

### Multi-Agent Coordination

```typescript
export function WorkflowWithMultipleAgents() {
  // Agent 1: Data processing
  const processor = useStream({ assistantId: "data_processing_agent" });

  // Agent 2: Analysis
  const analyzer = useStream({ assistantId: "analysis_agent" });

  const handleWorkflow = async (file: File) => {
    // Step 1: Process with agent 1
    await processor.submitMessage({
      content: `Process this file: ${file.name}`
    });

    // Step 2: Analyze with agent 2
    await analyzer.submitMessage({
      content: "Analyze the processed data"
    });
  };

  return <WorkflowUI onSubmit={handleWorkflow} />;
}
```

## State Management

### Local State (Simple)

```typescript
export function Component() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    const result = await api.getData();
    setData(result);
    setLoading(false);
  };

  return <div>{data && <Display data={data} />}</div>;
}
```

### Context + Zustand (Complex)

```typescript
// store/useAppStore.ts
import { create } from 'zustand';

export const useAppStore = create((set) => ({
  datasets: [],
  selectedDataset: null,
  setDatasets: (datasets) => set({ datasets }),
  selectDataset: (dataset) => set({ selectedDataset: dataset }),
}));

// component.tsx
export function DatasetBrowser() {
  const { datasets, selectedDataset, selectDataset } = useAppStore();

  return (
    <div>
      {datasets.map(ds => (
        <div key={ds.id} onClick={() => selectDataset(ds)}>
          {ds.name}
        </div>
      ))}
      {selectedDataset && <DatasetDetails dataset={selectedDataset} />}
    </div>
  );
}
```

## Routing with Next.js App Router

### File-Based Routing

```
src/app/
├── page.tsx              → / (home)
├── chat/
│   └── page.tsx          → /chat
├── datasets/
│   ├── page.tsx          → /datasets (list)
│   └── [id]/
│       └── page.tsx      → /datasets/123 (details)
└── admin/
    └── page.tsx          → /admin
```

### Dynamic Routes

```typescript
// src/app/datasets/[id]/page.tsx
export default function DatasetDetail({ params }: { params: { id: string } }) {
  const [dataset, setDataset] = useState(null);

  useEffect(() => {
    fetchDataset(params.id).then(setDataset);
  }, [params.id]);

  return <div>{dataset && <DatasetView dataset={dataset} />}</div>;
}
```

## Styling Patterns

### Tailwind CSS (Recommended)

```typescript
<div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
  <h2 className="text-2xl font-bold text-gray-900 mb-4">Title</h2>
  <p className="text-gray-600">Description</p>
</div>
```

### CSS Modules

```typescript
// Component.module.css
.container { background: white; padding: 24px; }
.title { font-size: 24px; font-weight: bold; }

// Component.tsx
import styles from './Component.module.css';
<div className={styles.container}>
  <h2 className={styles.title}>Title</h2>
</div>
```

### shadcn/ui Components

```typescript
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

<Button variant="default" size="lg">Click me</Button>
<Card><CardContent>Content</CardContent></Card>
```

## Best Practices

1. **Keep chat and business logic separate** - Use `/page.tsx` for chat, custom routes for business
2. **Use environment variables for configuration** - Don't hardcode URLs
3. **Handle loading and error states** - Provide feedback to users
4. **Implement proper TypeScript types** - Type safety prevents bugs
5. **Use React hooks for state** - useState, useEffect, useContext, useMemo, useCallback
6. **Optimize re-renders** - useMemo for expensive computations, useCallback for callbacks
7. **Implement error boundaries** - Catch React errors gracefully
8. **Use proper data fetching** - Consider React Query or SWR for server state
9. **Implement proper SEO** - Next.js metadata API for page metadata
10. **Test responsively** - Ensure mobile compatibility
