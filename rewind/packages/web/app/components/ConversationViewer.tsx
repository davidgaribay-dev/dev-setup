import { ArrowLeft, Monitor, User, Network, Server } from 'lucide-react';
import type { Conversation } from '~/lib/types';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { ChatMessage } from './ChatMessage';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { MonacoCodeBlock } from './MonacoCodeBlock';
import { formatNumber, formatModelName, safeFormatDate } from '~/lib/stats';

interface ConversationViewerProps {
  conversation: Conversation;
  onBack: () => void;
}

export function ConversationViewer({ conversation, onBack }: ConversationViewerProps) {
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center gap-4 mb-3">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h2 className="text-xl font-bold">Conversation Details</h2>
        </div>
        <div className="flex items-center gap-2 flex-wrap ml-12">
          <span className="text-sm text-muted-foreground">
            {safeFormatDate(conversation.timestamp, 'MMM dd, yyyy HH:mm')}
          </span>
          <span className="text-muted-foreground">•</span>
          <Badge variant="outline">{conversation.messageCount} messages</Badge>
          {conversation.model && (
            <>
              <span className="text-muted-foreground">•</span>
              <Badge>{formatModelName(conversation.model)}</Badge>
            </>
          )}
          {conversation.totalTokens && (
            <>
              <span className="text-muted-foreground">•</span>
              <Badge variant="secondary">{formatNumber(conversation.totalTokens)} tokens</Badge>
            </>
          )}
          {(conversation.hostname || conversation.username) && (
            <>
              <span className="text-muted-foreground">•</span>
              <span className="text-sm text-muted-foreground">
                {conversation.username && conversation.hostname
                  ? `${conversation.username}@${conversation.hostname}`
                  : conversation.hostname || conversation.username}
                {conversation.ipAddress && ` (${conversation.ipAddress})`}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Content */}
      <Tabs defaultValue="formatted" className="flex-1 flex flex-col min-h-0">
        <div className="border-b px-4">
          <TabsList>
            <TabsTrigger value="formatted">Conversation</TabsTrigger>
            <TabsTrigger value="raw">Raw JSON</TabsTrigger>
            <TabsTrigger value="stats">Statistics</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="formatted" className="flex-1 min-h-0 mt-0">
          <ScrollArea className="h-full">
            <div className="py-2">
              {conversation.messages.map(msg => (
                <ChatMessage key={msg.uuid} message={msg} />
              ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="raw" className="flex-1 min-h-0 mt-0 overflow-hidden">
          <div className="h-full p-6">
            <MonacoCodeBlock
              code={JSON.stringify(conversation, null, 2)}
              language="json"
              maxHeight={9999}
            />
          </div>
        </TabsContent>

        <TabsContent value="stats" className="flex-1 min-h-0 mt-0 p-6">
          <ScrollArea className="h-full">
            <div className="space-y-4">
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground mb-1">Total Messages</div>
                  <div className="text-2xl font-bold">{conversation.messageCount}</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground mb-1">User Messages</div>
                  <div className="text-2xl font-bold">
                    {conversation.messages.filter(m => m.type === 'user').length}
                  </div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground mb-1">Assistant Messages</div>
                  <div className="text-2xl font-bold">
                    {conversation.messages.filter(m => m.type === 'assistant').length}
                  </div>
                </div>
                {conversation.totalTokens && (
                  <div className="p-4 border rounded-lg">
                    <div className="text-sm text-muted-foreground mb-1">Total Tokens</div>
                    <div className="text-2xl font-bold">
                      {formatNumber(conversation.totalTokens)}
                    </div>
                  </div>
                )}
                {conversation.inputTokens && (
                  <div className="p-4 border rounded-lg">
                    <div className="text-sm text-muted-foreground mb-1">Input Tokens</div>
                    <div className="text-2xl font-bold">
                      {formatNumber(conversation.inputTokens)}
                    </div>
                  </div>
                )}
                {conversation.outputTokens && (
                  <div className="p-4 border rounded-lg">
                    <div className="text-sm text-muted-foreground mb-1">Output Tokens</div>
                    <div className="text-2xl font-bold">
                      {formatNumber(conversation.outputTokens)}
                    </div>
                  </div>
                )}
              </div>

              {/* Enterprise Metadata Section */}
              {(conversation.hostname || conversation.username || conversation.ipAddress || conversation.platform) && (
                <div className="mt-6">
                  <h3 className="text-sm font-medium text-muted-foreground mb-3">Client Information</h3>
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                    {conversation.hostname && (
                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                          <Server className="h-3.5 w-3.5" />
                          <span>Hostname</span>
                        </div>
                        <div className="text-lg font-medium truncate" title={conversation.hostname}>
                          {conversation.hostname}
                        </div>
                      </div>
                    )}
                    {conversation.username && (
                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                          <User className="h-3.5 w-3.5" />
                          <span>User</span>
                        </div>
                        <div className="text-lg font-medium truncate" title={conversation.username}>
                          {conversation.username}
                        </div>
                      </div>
                    )}
                    {conversation.ipAddress && (
                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                          <Network className="h-3.5 w-3.5" />
                          <span>IP Address</span>
                        </div>
                        <div className="text-lg font-medium font-mono">
                          {conversation.ipAddress}
                        </div>
                      </div>
                    )}
                    {conversation.platform && (
                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                          <Monitor className="h-3.5 w-3.5" />
                          <span>Platform</span>
                        </div>
                        <div className="text-lg font-medium">
                          {conversation.platform}
                          {conversation.osVersion && (
                            <span className="text-sm text-muted-foreground ml-1">
                              ({conversation.osVersion})
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                    {conversation.team && (
                      <div className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">Team</div>
                        <div className="text-lg font-medium">{conversation.team}</div>
                      </div>
                    )}
                    {conversation.environment && (
                      <div className="p-4 border rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">Environment</div>
                        <div className="text-lg font-medium">{conversation.environment}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}
