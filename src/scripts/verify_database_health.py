#!/usr/bin/env python3
"""
Database Health Verification Script
Verifies connectivity and health status for PostgreSQL and Redis databases.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


def check_database_dependencies() -> Dict[str, bool]:
    """
    Check if required database libraries are installed.

    Returns:
        Dictionary with installation status for each library
    """
    dependencies = {"psycopg2": False, "redis": False}

    # Check psycopg2
    try:
        import psycopg2

        dependencies["psycopg2"] = True
    except ImportError:
        print(
            "Warning: psycopg2 not installed. PostgreSQL health check will be skipped."
        )
        print("Install with: pip install psycopg2-binary")

    # Check redis
    try:
        import redis

        dependencies["redis"] = True
    except ImportError:
        print("Warning: redis not installed. Redis health check will be skipped.")
        print("Install with: pip install redis")

    return dependencies


def load_database_config(config_path: Path) -> Dict:
    """
    Load database configuration from JSON file.

    Args:
        config_path: Path to the configuration JSON file

    Returns:
        Dictionary containing database configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)

    return config


def verify_postgresql_connection(
    config: Dict, timeout: int = 5
) -> Tuple[bool, str, Optional[float]]:
    """
    Verify PostgreSQL database connection.

    Args:
        config: PostgreSQL configuration dictionary
        timeout: Connection timeout in seconds

    Returns:
        Tuple of (is_healthy, status_message, response_time)
    """
    try:
        import psycopg2
        from psycopg2 import OperationalError

        username = config["username"]
        password = config["password"]
        database = config["database"]
        host = config["host"]
        port = config["port"]

        start_time = time.time()

        # Create connection string
        if password:
            conn_string = f"dbname={database} user={username} password={password} host={host} port={port} connect_timeout={timeout}"
        else:
            conn_string = f"dbname={database} user={username} host={host} port={port} connect_timeout={timeout}"

        # Attempt connection
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Execute a simple query to verify functionality
        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        cursor.close()
        conn.close()

        response_time = time.time() - start_time

        return (
            True,
            f"PostgreSQL connected successfully - Version: {version[0][:50]}",
            response_time,
        )

    except ImportError:
        return False, "psycopg2 library not installed", None
    except Exception as e:
        return False, f"PostgreSQL connection failed: {str(e)}", None


def verify_redis_connection(
    config: Dict, timeout: int = 5
) -> Tuple[bool, str, Optional[float]]:
    """
    Verify Redis database connection.

    Args:
        config: Redis configuration dictionary
        timeout: Connection timeout in seconds

    Returns:
        Tuple of (is_healthy, status_message, response_time)
    """
    try:
        import redis

        host = config["host"]
        port = config["port"]
        db = config["database"]
        password = config.get("password", None)
        username = config.get("username", None)

        start_time = time.time()

        # Build connection parameters
        connection_params = {
            "host": host,
            "port": port,
            "db": db,
            "socket_timeout": timeout,
            "socket_connect_timeout": timeout,
        }

        if password:
            connection_params["password"] = password
        if username:
            connection_params["username"] = username

        # Attempt connection
        r = redis.Redis(**connection_params)

        # Test connection with PING
        response = r.ping()

        # Get server info
        info = r.info("server")
        version = info.get("redis_version", "unknown")

        # Get memory info
        memory_info = r.info("memory")
        used_memory = memory_info.get("used_memory_human", "unknown")

        response_time = time.time() - start_time

        return (
            True,
            f"Redis connected successfully - Version: {version}, Memory: {used_memory}",
            response_time,
        )

    except ImportError:
        return False, "redis library not installed", None
    except redis.exceptions.ConnectionError as e:
        return False, f"Redis connection failed: {str(e)}", None
    except Exception as e:
        return False, f"Redis error: {str(e)}", None


def verify_postgresql(config: Dict, timeout: int = 5) -> Dict:
    """
    Verify PostgreSQL database health.

    Args:
        config: PostgreSQL configuration dictionary
        timeout: Connection timeout in seconds

    Returns:
        Dictionary with verification results
    """
    print(f"\n{'='*60}")
    print(f"Verifying PostgreSQL")
    print(f"Host: {config['host']}:{config['port']}")
    print(f"Database: {config['database']}")
    print(f"User: {config['username']}")
    print(f"{'='*60}")

    start_time = time.time()
    is_healthy, status_message, response_time = verify_postgresql_connection(
        config, timeout
    )
    elapsed_time = time.time() - start_time

    result = {
        "database_type": "PostgreSQL",
        "host": config["host"],
        "port": config["port"],
        "database": config["database"],
        "username": config["username"],
        "is_healthy": is_healthy,
        "status": "HEALTHY" if is_healthy else "UNHEALTHY",
        "message": status_message,
        "response_time": f"{response_time:.3f}s" if response_time else "N/A",
        "timestamp": datetime.now().isoformat(),
    }

    # Print results
    status_symbol = "✓" if is_healthy else "✗"
    print(f"Status: {status_symbol} {result['status']}")
    print(f"Message: {status_message}")
    if response_time:
        print(f"Response Time: {response_time:.3f}s")
    print(f"{'='*60}")

    return result


def verify_redis(config: Dict, timeout: int = 5) -> Dict:
    """
    Verify Redis database health.

    Args:
        config: Redis configuration dictionary
        timeout: Connection timeout in seconds

    Returns:
        Dictionary with verification results
    """
    print(f"\n{'='*60}")
    print(f"Verifying Redis")
    print(f"Host: {config['host']}:{config['port']}")
    print(f"Database: {config['database']}")
    print(f"{'='*60}")

    start_time = time.time()
    is_healthy, status_message, response_time = verify_redis_connection(config, timeout)
    elapsed_time = time.time() - start_time

    result = {
        "database_type": "Redis",
        "host": config["host"],
        "port": config["port"],
        "database": config["database"],
        "is_healthy": is_healthy,
        "status": "HEALTHY" if is_healthy else "UNHEALTHY",
        "message": status_message,
        "response_time": f"{response_time:.3f}s" if response_time else "N/A",
        "timestamp": datetime.now().isoformat(),
    }

    # Print results
    status_symbol = "✓" if is_healthy else "✗"
    print(f"Status: {status_symbol} {result['status']}")
    print(f"Message: {status_message}")
    if response_time:
        print(f"Response Time: {response_time:.3f}s")
    print(f"{'='*60}")

    return result


def verify_all_databases(config_path: str, timeout: int = 5) -> Dict:
    """
    Verify all databases in the configuration.

    Args:
        config_path: Path to database configuration JSON file
        timeout: Connection timeout per database in seconds

    Returns:
        Dictionary with overall results and per-database details
    """
    config_path_obj = Path(config_path)
    config = load_database_config(config_path_obj)

    print("\n" + "=" * 60)
    print("Database Health Verification")
    print("=" * 60)

    # Check dependencies
    dependencies = check_database_dependencies()

    results = []
    healthy_count = 0
    unhealthy_count = 0

    # Verify PostgreSQL if psycopg2 is available
    if "postgresql" in config and dependencies["psycopg2"]:
        result = verify_postgresql(config["postgresql"], timeout)
        results.append(result)

        if result["is_healthy"]:
            healthy_count += 1
        else:
            unhealthy_count += 1
    elif "postgresql" in config and not dependencies["psycopg2"]:
        print("\nSkipping PostgreSQL health check - psycopg2 not installed")

    # Verify Redis if redis library is available
    if "redis" in config and dependencies["redis"]:
        result = verify_redis(config["redis"], timeout)
        results.append(result)

        if result["is_healthy"]:
            healthy_count += 1
        else:
            unhealthy_count += 1
    elif "redis" in config and not dependencies["redis"]:
        print("\nSkipping Redis health check - redis not installed")

    # Print summary
    if results:
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Total Databases: {len(results)}")
        print(f"Healthy: {healthy_count} ✓")
        print(f"Unhealthy: {unhealthy_count} ✗")
        print(f"Health Rate: {(healthy_count / len(results) * 100):.1f}%")
        print("=" * 60)

    return {
        "total_databases": len(results),
        "healthy_count": healthy_count,
        "unhealthy_count": unhealthy_count,
        "health_rate": f"{(healthy_count / len(results) * 100):.1f}%"
        if results
        else "N/A",
        "timestamp": datetime.now().isoformat(),
        "databases": results,
    }


def main():
    """Main entry point for the database verification script."""
    # Default configuration path
    default_config_path = (
        Path(__file__).parent.parent.parent / "config" / "database.json"
    )

    # Allow command-line override
    config_path = sys.argv[1] if len(sys.argv) > 1 else str(default_config_path)

    try:
        results = verify_all_databases(config_path, timeout=5)

        # Exit with appropriate code
        if results["unhealthy_count"] > 0:
            sys.exit(1)  # Exit with error if any databases are unhealthy
        else:
            sys.exit(0)  # Exit successfully if all databases are healthy

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\nError: Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: Unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
