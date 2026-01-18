import neo4j, { Driver, Session } from 'neo4j-driver';

// Single driver instance for the application (connection pooling handled internally)
let driver: Driver | null = null;

export function getDriver(): Driver {
  if (!driver) {
    const uri = process.env.NEO4J_URI || 'bolt://localhost:7687';
    const user = process.env.NEO4J_USER || 'neo4j';
    const password = process.env.NEO4J_PASSWORD || 'rewind_dev_password';

    driver = neo4j.driver(uri, neo4j.auth.basic(user, password), {
      maxConnectionPoolSize: 50,
      connectionAcquisitionTimeout: 30000,
      maxTransactionRetryTime: 30000,
      logging: neo4j.logging.console(process.env.LOG_LEVEL === 'debug' ? 'debug' : 'warn'),
    });
  }
  return driver;
}

export function getSession(database = 'neo4j'): Session {
  return getDriver().session({ database });
}

export async function closeDriver(): Promise<void> {
  if (driver) {
    await driver.close();
    driver = null;
  }
}

export async function verifyConnection(): Promise<boolean> {
  try {
    await getDriver().verifyConnectivity();
    return true;
  } catch (error) {
    console.error('Neo4j connection failed:', error);
    return false;
  }
}

/**
 * Initialize database schema with constraints and indexes.
 *
 * Best practices applied:
 * 1. Unique constraints on identifying properties (enables efficient MERGE)
 * 2. Indexes on frequently queried properties
 * 3. Composite index for ContentBlock deduplication
 *
 * @see https://neo4j.com/docs/getting-started/data-modeling/modeling-tips/
 */
export async function initializeSchema(): Promise<void> {
  const session = getSession();
  try {
    // Unique constraints - critical for MERGE performance
    // Without these, MERGE does a full label scan each time
    const constraints = [
      // Project uniqueness by ID
      `CREATE CONSTRAINT rewind_project_id IF NOT EXISTS
       FOR (p:Rewind_Project) REQUIRE p.id IS UNIQUE`,

      // Conversation uniqueness by sessionId
      `CREATE CONSTRAINT rewind_conversation_session_id IF NOT EXISTS
       FOR (c:Rewind_Conversation) REQUIRE c.sessionId IS UNIQUE`,

      // Message uniqueness by UUID
      `CREATE CONSTRAINT rewind_message_uuid IF NOT EXISTS
       FOR (m:Rewind_Message) REQUIRE m.uuid IS UNIQUE`,

      // ContentBlock uniqueness by messageUuid + index (composite)
      `CREATE CONSTRAINT rewind_content_block_unique IF NOT EXISTS
       FOR (b:Rewind_ContentBlock) REQUIRE (b.messageUuid, b.index) IS UNIQUE`,
    ];

    // Indexes for query performance
    const indexes = [
      // Message timestamp for ordering
      `CREATE INDEX rewind_message_timestamp IF NOT EXISTS
       FOR (m:Rewind_Message) ON (m.timestamp)`,

      // Message type for filtering
      `CREATE INDEX rewind_message_type IF NOT EXISTS
       FOR (m:Rewind_Message) ON (m.type)`,

      // Conversation timestamp for ordering
      `CREATE INDEX rewind_conversation_timestamp IF NOT EXISTS
       FOR (c:Rewind_Conversation) ON (c.timestamp)`,

      // Project path for lookups
      `CREATE INDEX rewind_project_path IF NOT EXISTS
       FOR (p:Rewind_Project) ON (p.path)`,
    ];

    // Execute all constraint and index creations
    for (const query of [...constraints, ...indexes]) {
      try {
        await session.run(query);
      } catch (error) {
        // Ignore errors for constraints/indexes that already exist
        const message = error instanceof Error ? error.message : String(error);
        if (!message.includes('already exists')) {
          console.error(`Schema initialization warning: ${message}`);
        }
      }
    }

    // Wait for indexes to be online
    await session.run('CALL db.awaitIndexes()');

    console.log('Database schema initialized successfully');
  } finally {
    await session.close();
  }
}

// Re-export neo4j for integer handling
export { neo4j };
