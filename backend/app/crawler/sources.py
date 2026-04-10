from dataclasses import dataclass, field


@dataclass
class BlogSource:
    name: str
    company: str
    url: str
    feed_url: str | None
    feed_type: str  # "rss" | "scrape"
    topic_hints: list[str] = field(default_factory=list)
    crawl_limit: int = 30


SOURCES: list[BlogSource] = [
    BlogSource(
        name="Google Research Blog",
        company="Google",
        url="https://research.google/blog/",
        feed_url="https://research.google/blog/rss/",
        feed_type="rss",
        topic_hints=["distributed", "systems", "infrastructure", "ml", "database"],
    ),
    BlogSource(
        name="Google Cloud Blog",
        company="Google",
        url="https://cloud.google.com/blog/",
        feed_url="https://cloudblog.withgoogle.com/rss/",
        feed_type="rss",
        topic_hints=["distributed", "cloud", "kubernetes", "spanner", "bigtable"],
    ),
    BlogSource(
        name="Meta Engineering Blog",
        company="Meta",
        url="https://engineering.fb.com/",
        feed_url="https://engineering.fb.com/feed/",
        feed_type="rss",
        topic_hints=["distributed", "infrastructure", "database", "networking", "systems"],
    ),
    BlogSource(
        name="Netflix Tech Blog",
        company="Netflix",
        url="https://netflixtechblog.com/",
        feed_url="https://netflixtechblog.com/feed",
        feed_type="rss",
        topic_hints=["distributed", "microservice", "resilience", "cassandra", "scalability"],
    ),
    BlogSource(
        name="Uber Engineering",
        company="Uber",
        url="https://eng.uber.com/",
        feed_url="https://eng.uber.com/feed/",
        feed_type="rss",
        topic_hints=["distributed", "database", "kafka", "microservice", "real-time"],
    ),
    BlogSource(
        name="Airbnb Engineering",
        company="Airbnb",
        url="https://medium.com/airbnb-engineering",
        feed_url="https://medium.com/feed/airbnb-engineering",
        feed_type="rss",
        topic_hints=["distributed", "data", "infrastructure", "scalability"],
    ),
    BlogSource(
        name="LinkedIn Engineering",
        company="LinkedIn",
        url="https://engineering.linkedin.com/blog",
        feed_url="https://engineering.linkedin.com/blog.rss",
        feed_type="rss",
        topic_hints=["distributed", "kafka", "samza", "database", "infrastructure"],
    ),
    BlogSource(
        name="AWS Architecture Blog",
        company="AWS",
        url="https://aws.amazon.com/blogs/architecture/",
        feed_url="https://aws.amazon.com/blogs/architecture/feed/",
        feed_type="rss",
        topic_hints=["distributed", "cloud", "architecture", "database", "serverless"],
    ),
    BlogSource(
        name="AWS Database Blog",
        company="AWS",
        url="https://aws.amazon.com/blogs/database/",
        feed_url="https://aws.amazon.com/blogs/database/feed/",
        feed_type="rss",
        topic_hints=["database", "dynamodb", "rds", "aurora", "distributed"],
    ),
    BlogSource(
        name="Microsoft Engineering Blog",
        company="Microsoft",
        url="https://devblogs.microsoft.com/engineering-at-microsoft/",
        feed_url="https://devblogs.microsoft.com/engineering-at-microsoft/feed/",
        feed_type="rss",
        topic_hints=["distributed", "azure", "systems", "infrastructure", "database"],
    ),
    BlogSource(
        name="Cloudflare Blog",
        company="Cloudflare",
        url="https://blog.cloudflare.com/",
        feed_url="https://blog.cloudflare.com/rss/",
        feed_type="rss",
        topic_hints=["networking", "distributed", "cdn", "dns", "infrastructure", "security"],
    ),
    BlogSource(
        name="Stripe Engineering",
        company="Stripe",
        url="https://stripe.com/blog/engineering",
        feed_url="https://stripe.com/blog/engineering.rss",
        feed_type="rss",
        topic_hints=["distributed", "database", "reliability", "infrastructure", "payments"],
    ),
    BlogSource(
        name="Dropbox Tech Blog",
        company="Dropbox",
        url="https://dropbox.tech/",
        feed_url="https://dropbox.tech/feed",
        feed_type="rss",
        topic_hints=["distributed", "storage", "infrastructure", "database", "synchronization"],
    ),
    BlogSource(
        name="Discord Engineering",
        company="Discord",
        url="https://discord.com/category/engineering",
        feed_url=None,
        feed_type="scrape",
        topic_hints=["distributed", "database", "scalability", "rust", "elixir"],
    ),
    BlogSource(
        name="Databricks Engineering",
        company="Databricks",
        url="https://www.databricks.com/blog/category/engineering",
        feed_url="https://www.databricks.com/feed",
        feed_type="rss",
        topic_hints=["spark", "distributed", "data", "lakehouse", "delta"],
    ),
    BlogSource(
        name="Confluent Blog",
        company="Confluent",
        url="https://www.confluent.io/blog/",
        feed_url="https://www.confluent.io/feed/",
        feed_type="rss",
        topic_hints=["kafka", "streaming", "distributed", "event", "messaging"],
    ),
    BlogSource(
        name="Pinterest Engineering",
        company="Pinterest",
        url="https://medium.com/pinterest-engineering",
        feed_url="https://medium.com/feed/pinterest-engineering",
        feed_type="rss",
        topic_hints=["distributed", "scalability", "infrastructure", "database"],
    ),
    BlogSource(
        name="Shopify Engineering",
        company="Shopify",
        url="https://shopify.engineering/",
        feed_url="https://shopify.engineering/blog.atom",
        feed_type="rss",
        topic_hints=["distributed", "scalability", "database", "rails", "infrastructure"],
    ),
]

# Keywords for relevance filtering (Stage 1 — free, no API cost)
RELEVANCE_KEYWORDS: set[str] = {
    # Core distributed systems
    "distributed", "consensus", "raft", "paxos", "replication",
    "consistency", "eventual consistency", "strong consistency",
    "sharding", "partition", "partitioning", "horizontal scaling",
    "vertical scaling", "scalability", "scale",
    # Architecture patterns
    "microservice", "microservices", "service mesh", "sidecar",
    "event sourcing", "cqrs", "saga", "circuit breaker",
    "load balanc", "rate limit",
    # Protocols and algorithms
    "two-phase commit", "2pc", "three-phase", "vector clock",
    "crdt", "gossip", "heartbeat", "leader election",
    "cap theorem", "acid", "base",
    # Databases
    "database", "nosql", "sql", "relational", "key-value",
    "cassandra", "dynamodb", "spanner", "cockroach", "tidb",
    "postgres", "mysql", "mongodb", "redis", "rocksdb",
    "lsm", "b-tree", "wal", "write-ahead log",
    "transaction", "isolation", "mvcc", "lock",
    # Messaging/Streaming
    "kafka", "kinesis", "pubsub", "message queue",
    "streaming", "flink", "spark", "storm",
    # Infrastructure
    "kubernetes", "k8s", "container", "docker",
    "infrastructure", "infra", "reliability", "availability",
    "fault tolerance", "failover", "disaster recovery",
    "latency", "throughput", "performance", "benchmark",
    "sla", "slo", "sli", "observability", "monitoring",
    # Networking
    "cdn", "dns", "grpc", "thrift", "rpc", "tcp", "udp",
    "networking", "protocol", "bandwidth", "anycast",
    # Storage
    "storage", "blob", "object store", "file system",
    "hdfs", "s3", "ceph", "distributed file",
    # Cloud native
    "serverless", "lambda", "cloud native", "multi-cloud",
    "region", "availability zone",
}
