// Core data types based on Claude Code conversation structure and Anthropic Messages API

export interface Usage {
  input_tokens: number;
  cache_creation_input_tokens?: number;
  cache_read_input_tokens?: number;
  cache_creation?: {
    ephemeral_5m_input_tokens?: number;
    ephemeral_1h_input_tokens?: number;
  };
  output_tokens: number;
  service_tier?: string;
}

// Anthropic API Content Block Types

export interface TextBlock {
  type: 'text';
  text: string;
}

export interface ToolUseBlock {
  type: 'tool_use';
  id: string;
  name: string;
  input: Record<string, unknown>;
}

export interface ToolResultBlock {
  type: 'tool_result';
  tool_use_id: string;
  content: string;
  is_error?: boolean;
}

export interface ThinkingBlock {
  type: 'thinking';
  thinking: string;
}

export type ContentBlock = TextBlock | ToolUseBlock | ToolResultBlock | ThinkingBlock;

// Legacy type for backwards compatibility
export interface MessageContent {
  type: string;
  text?: string;
  [key: string]: unknown;
}

export interface AssistantMessage {
  model: string;
  id: string;
  type: string;
  role: string;
  content: ContentBlock[];
  stop_reason: 'end_turn' | 'max_tokens' | 'stop_sequence' | 'tool_use' | null;
  stop_sequence: string | null;
  usage: Usage;
}

export interface UserMessage {
  role: string;
  content: string | ContentBlock[];
}

// Conversation message from transcript
export interface ConversationMessage {
  parentUuid: string | null;
  isSidechain?: boolean;
  userType?: string;
  cwd: string;
  sessionId: string;
  version: string;
  gitBranch?: string;
  agentId?: string;
  type: 'user' | 'assistant' | 'queue-operation';
  message: UserMessage | AssistantMessage;
  requestId?: string;
  uuid: string;
  timestamp: string;
  usage?: Usage;
}

// Frontend types

export interface Conversation {
  sessionId: string;
  uuid: string;
  timestamp: Date;
  messageCount: number;
  preview: string;
  type: 'user' | 'assistant' | 'queue-operation';
  messages: ConversationMessage[];
  model?: string;
  totalTokens?: number;
  inputTokens?: number;
  outputTokens?: number;
  // Enterprise metadata (captured from client VM)
  hostname?: string;
  ipAddress?: string;
  username?: string;
  platform?: string;
  osVersion?: string;
  team?: string;
  environment?: string;
}

export interface Project {
  id: string;
  name?: string;
  displayName: string;
  conversationCount: number;
  totalMessages?: number;
  lastModified: Date;
  path: string;
  conversations?: Conversation[];
}

export interface Stats {
  totalConversations: number;
  totalProjects: number;
  totalMessages: number;
  userMessageCount: number;
  assistantMessageCount: number;
  totalTokens: number;
  inputTokens: number;
  outputTokens: number;
  mostUsedModel: string;
  modelUsageCount: number;
  modelDistribution: Record<string, number>;
  timelineData: { date: string; count: number }[];
}
