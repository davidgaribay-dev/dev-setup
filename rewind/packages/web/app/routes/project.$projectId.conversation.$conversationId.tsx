import { useParams, useNavigate } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import type { Route } from './+types/project.$projectId.conversation.$conversationId';
import { useProjects } from '~/hooks/useProjects';
import { getConversationById } from '~/lib/api-client';
import { AppSidebar } from '~/components/AppSidebar';
import { ChatMessage } from '~/components/ChatMessage';
import { MonacoCodeBlock } from '~/components/MonacoCodeBlock';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import { ScrollArea } from '~/components/ui/scroll-area';
import { Separator } from '~/components/ui/separator';
import {
  RefreshCw,
  PanelRight,
  Code,
  MessageSquare,
  Calendar,
  Hash,
  Cpu,
  Sparkles,
  Clock,
  Wrench,
  Server,
  User,
  Network,
  Monitor,
} from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import { formatModelName, safeFormatDate, formatNumber } from '~/lib/stats';

export function meta({ params }: Route.MetaArgs) {
  return [
    { title: `Conversation - Rewind` },
    {
      name: 'description',
      content:
        'View detailed conversation history with messages, code blocks, thinking processes, and token usage statistics',
    },
  ];
}

export default function ConversationDetail() {
  const { projectId, conversationId } = useParams();
  const navigate = useNavigate();
  const { projects, loading: projectsLoading } = useProjects();

  // Persist UI state in localStorage
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('rewind:sidebarCollapsed') === 'true';
    }
    return false;
  });
  const [showProperties, setShowProperties] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('rewind:showProperties') !== 'false';
    }
    return true;
  });
  const [activeTab, setActiveTab] = useState<string>('conversation');

  // Save UI state to localStorage
  useEffect(() => {
    localStorage.setItem('rewind:sidebarCollapsed', String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  useEffect(() => {
    localStorage.setItem('rewind:showProperties', String(showProperties));
  }, [showProperties]);

  const project = projects.find((p) => p.id === projectId);

  // Fetch conversation details
  const { data: conversationData, isLoading: conversationLoading } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => getConversationById(conversationId!),
    enabled: !!conversationId,
    staleTime: 30 * 1000,
  });

  if (projectsLoading || conversationLoading) {
    return (
      <div className="h-screen flex">
        <AppSidebar collapsed={sidebarCollapsed} onCollapsedChange={setSidebarCollapsed} />
        <div className="flex-1 flex items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (!conversationData || !project) {
    return (
      <div className="h-screen flex">
        <AppSidebar collapsed={sidebarCollapsed} onCollapsedChange={setSidebarCollapsed} />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-2">Conversation not found</h2>
            <p className="text-muted-foreground mb-4">
              The conversation you're looking for doesn't exist.
            </p>
            <Button onClick={() => navigate(`/project/${projectId}`)}>Back to Project</Button>
          </div>
        </div>
      </div>
    );
  }

  // Extract preview from first user message
  let preview = '';
  const firstUserMsg = conversationData.messages?.find((m) => m.type === 'user');
  if (firstUserMsg?.message?.content) {
    const content = firstUserMsg.message.content;
    if (typeof content === 'string') {
      preview = content.slice(0, 200);
    } else if (Array.isArray(content)) {
      const textBlock = content.find((b: { type: string }) => b.type === 'text');
      if (textBlock && 'text' in textBlock) {
        preview = (textBlock as { text: string }).text.slice(0, 200);
      }
    }
  }

  const conversation = {
    uuid: conversationData.uuid,
    sessionId: conversationData.sessionId,
    timestamp: new Date(conversationData.timestamp),
    messageCount: conversationData.messageCount,
    preview: preview || conversationData.preview || 'Untitled',
    type: conversationData.type as 'user' | 'assistant',
    messages: conversationData.messages || [],
    model: conversationData.model,
    totalTokens: conversationData.totalTokens,
    inputTokens: conversationData.inputTokens,
    outputTokens: conversationData.outputTokens,
    // Enterprise metadata
    hostname: conversationData.hostname,
    username: conversationData.username,
    ipAddress: conversationData.ipAddress,
    platform: conversationData.platform,
    osVersion: conversationData.osVersion,
    team: conversationData.team,
    environment: conversationData.environment,
  };

  // Calculate tool usage stats
  const toolUsage: Record<string, number> = {};
  conversation.messages.forEach((msg) => {
    if (msg.type === 'assistant' && Array.isArray(msg.message?.content)) {
      msg.message.content.forEach((block: { type: string; name?: string }) => {
        if (block.type === 'tool_use' && block.name) {
          toolUsage[block.name] = (toolUsage[block.name] || 0) + 1;
        }
      });
    }
  });

  const totalToolCalls = Object.values(toolUsage).reduce((a, b) => a + b, 0);

  return (
    <TooltipProvider delayDuration={0}>
      <div className="h-screen flex overflow-hidden">
        {/* Left Sidebar - Navigation */}
        <AppSidebar collapsed={sidebarCollapsed} onCollapsedChange={setSidebarCollapsed} />

        {/* Main Content */}
        <div className="flex-1 flex min-w-0">
          {/* Chat Content */}
          <div className="flex-1 flex flex-col min-w-0 relative">
            {/* Floating toggle button when panel is hidden */}
            {!showProperties && (
              <div className="absolute top-2 right-2 z-10">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      className="h-8 w-8 bg-background/80 backdrop-blur-sm"
                      onClick={() => setShowProperties(true)}
                    >
                      <PanelRight className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="left">Show properties</TooltipContent>
                </Tooltip>
              </div>
            )}

            {/* Content Area */}
            <div className="flex-1 min-h-0">
              {activeTab === 'conversation' ? (
                <ScrollArea className="h-full">
                  <div className="max-w-4xl mx-auto">
                    {conversation.messages.map((msg) => (
                      <ChatMessage key={msg.uuid} message={msg} />
                    ))}
                    {/* Bottom padding for scroll */}
                    <div className="h-8" />
                  </div>
                </ScrollArea>
              ) : (
                <div className="h-full p-4">
                  <MonacoCodeBlock
                    code={JSON.stringify(conversation, null, 2)}
                    language="json"
                    maxHeight={9999}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Right Panel - Linear-style Properties */}
          {showProperties && (
            <div className="w-72 border-l flex flex-col bg-muted/30">
              {/* Panel Header with controls */}
              <div className="h-12 flex items-center justify-between px-3 border-b">
                {/* Tab toggle buttons */}
                <div className="flex items-center bg-background rounded-lg p-0.5">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant={activeTab === 'conversation' ? 'secondary' : 'ghost'}
                        size="sm"
                        className="h-7 px-2.5"
                        onClick={() => setActiveTab('conversation')}
                      >
                        <MessageSquare className="h-3.5 w-3.5" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Conversation</TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant={activeTab === 'raw' ? 'secondary' : 'ghost'}
                        size="sm"
                        className="h-7 px-2.5"
                        onClick={() => setActiveTab('raw')}
                      >
                        <Code className="h-3.5 w-3.5" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Raw JSON</TooltipContent>
                  </Tooltip>
                </div>

                {/* Close button */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => setShowProperties(false)}
                    >
                      <PanelRight className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="left">Hide properties</TooltipContent>
                </Tooltip>
              </div>

              <ScrollArea className="flex-1">
                <div className="p-4 space-y-6">
                  {/* Title */}
                  <div>
                    <h2 className="text-sm font-semibold mb-1 line-clamp-2">
                      {conversation.preview}
                    </h2>
                    <p className="text-xs text-muted-foreground">
                      {project.displayName}
                    </p>
                  </div>

                  <Separator />

                  {/* Properties */}
                  <div className="space-y-4">
                    {/* Date */}
                    <PropertyRow
                      icon={Calendar}
                      label="Date"
                      value={safeFormatDate(conversation.timestamp, 'MMM d, yyyy')}
                    />

                    {/* Time */}
                    <PropertyRow
                      icon={Clock}
                      label="Time"
                      value={safeFormatDate(conversation.timestamp, 'HH:mm')}
                    />

                    {/* Model */}
                    {conversation.model && (
                      <PropertyRow
                        icon={Cpu}
                        label="Model"
                        value={
                          <Badge variant="secondary" className="text-xs font-normal">
                            {formatModelName(conversation.model)}
                          </Badge>
                        }
                      />
                    )}

                    {/* Messages */}
                    <PropertyRow
                      icon={MessageSquare}
                      label="Messages"
                      value={`${conversation.messageCount}`}
                    />

                    {/* Tokens */}
                    {conversation.totalTokens > 0 && (
                      <PropertyRow
                        icon={Sparkles}
                        label="Tokens"
                        value={formatNumber(conversation.totalTokens)}
                      />
                    )}

                    {/* Tool Calls */}
                    {totalToolCalls > 0 && (
                      <PropertyRow
                        icon={Wrench}
                        label="Tool Calls"
                        value={`${totalToolCalls}`}
                      />
                    )}

                    {/* Session ID */}
                    <PropertyRow
                      icon={Hash}
                      label="Session"
                      value={
                        <span className="font-mono text-xs truncate max-w-[120px]" title={conversation.sessionId}>
                          {conversation.sessionId.slice(0, 8)}...
                        </span>
                      }
                    />
                  </div>

                  {/* Client Information */}
                  {(conversation.hostname || conversation.username || conversation.ipAddress) && (
                    <>
                      <Separator />
                      <div>
                        <h3 className="text-xs font-medium text-muted-foreground mb-3">Client Information</h3>
                        <div className="space-y-4">
                          {conversation.hostname && (
                            <PropertyRow
                              icon={Server}
                              label="Hostname"
                              value={
                                <span className="text-xs truncate max-w-[120px]" title={conversation.hostname}>
                                  {conversation.hostname}
                                </span>
                              }
                            />
                          )}
                          {conversation.username && (
                            <PropertyRow
                              icon={User}
                              label="User"
                              value={conversation.username}
                            />
                          )}
                          {conversation.ipAddress && (
                            <PropertyRow
                              icon={Network}
                              label="IP Address"
                              value={
                                <span className="font-mono text-xs">{conversation.ipAddress}</span>
                              }
                            />
                          )}
                          {conversation.platform && (
                            <PropertyRow
                              icon={Monitor}
                              label="Platform"
                              value={
                                <span className="text-xs">
                                  {conversation.platform}
                                  {conversation.osVersion && ` (${conversation.osVersion})`}
                                </span>
                              }
                            />
                          )}
                          {conversation.team && (
                            <PropertyRow
                              icon={User}
                              label="Team"
                              value={conversation.team}
                            />
                          )}
                          {conversation.environment && (
                            <PropertyRow
                              icon={Server}
                              label="Environment"
                              value={
                                <Badge variant="outline" className="text-xs font-normal">
                                  {conversation.environment}
                                </Badge>
                              }
                            />
                          )}
                        </div>
                      </div>
                    </>
                  )}

                  {/* Token breakdown */}
                  {(conversation.inputTokens > 0 || conversation.outputTokens > 0) && (
                    <>
                      <Separator />
                      <div>
                        <h3 className="text-xs font-medium text-muted-foreground mb-3">Token Breakdown</h3>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Input</span>
                            <span className="font-mono">{formatNumber(conversation.inputTokens || 0)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Output</span>
                            <span className="font-mono">{formatNumber(conversation.outputTokens || 0)}</span>
                          </div>
                        </div>
                      </div>
                    </>
                  )}

                  {/* Tools used */}
                  {Object.keys(toolUsage).length > 0 && (
                    <>
                      <Separator />
                      <div>
                        <h3 className="text-xs font-medium text-muted-foreground mb-3">Tools Used</h3>
                        <div className="flex flex-wrap gap-1.5">
                          {Object.entries(toolUsage)
                            .sort(([, a], [, b]) => b - a)
                            .slice(0, 10)
                            .map(([tool, count]) => (
                              <Badge key={tool} variant="outline" className="text-xs font-normal">
                                {tool} <span className="ml-1 text-muted-foreground">{count}</span>
                              </Badge>
                            ))}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </ScrollArea>
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}

interface PropertyRowProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: React.ReactNode;
}

function PropertyRow({ icon: Icon, label, value }: PropertyRowProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Icon className="h-4 w-4" />
        <span className="text-sm">{label}</span>
      </div>
      <div className="text-sm">{value}</div>
    </div>
  );
}
