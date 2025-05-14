#!/usr/bin/env python3
import argparse
import logging
import sys
import os
import yaml

from flask import Flask, request, Response, jsonify

app = Flask(__name__)
logger = logging.getLogger("traefik-config-provider")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Global flag to control verbosity
VERBOSE_LOGGING = False

def deep_merge(dict1, dict2):
    """
    Recursively merge dict2 into dict1.
    If both dicts have a key pointing to a dictionary, merge them recursively.
    Otherwise, overwrite or add the key from dict2 to dict1.
    """
    for key, value in dict2.items():
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
            deep_merge(dict1[key], value)
        else:
            dict1[key] = value
    return dict1

def load_configs_from_api(namespace="traefik"):
    """
    Load configuration fragments by querying the Kubernetes API for all ConfigMaps
    with the label "traefik-config-fragment=true" in the specified namespace,
    merge them, and return the combined configuration.
    """
    try:
        from kubernetes import client, config
    except ImportError:
        logger.error("The kubernetes module is not installed. Please install it with 'pip install kubernetes'")
        return {}

    try:
        config.load_incluster_config()
        # Get a copy of the current configuration and disable SSL verification
        configuration = client.Configuration.get_default_copy()
        configuration.verify_ssl = False  # Disable SSL verification (not recommended for production)
        client.Configuration.set_default(configuration)
    except Exception as e:
        logger.error("Error loading in-cluster config: %s", e)
        return {}

    v1 = client.CoreV1Api()
    try:
        configmaps = v1.list_namespaced_config_map(
            namespace=namespace,
            label_selector="traefik-config-fragment=true"
        )
    except Exception as e:
        logger.error("Error listing ConfigMaps: %s", e)
        return {}

    combined_config = {}
    for cm in configmaps.items:
        if cm.data is None:
            continue
        for key, value in cm.data.items():
            try:
                fragment = yaml.safe_load(value)
                if fragment:
                    deep_merge(combined_config, fragment)
                    logger.info("Merged config fragment from ConfigMap '%s', key '%s'", cm.metadata.name, key)
            except Exception as e:
                logger.error("Error parsing config snippet from ConfigMap '%s': %s", cm.metadata.name, e)
    return combined_config

@app.before_request
def log_request_info():
    if VERBOSE_LOGGING:
        logger.info("=== Incoming Request ===")
        logger.info("Method: %s  URL: %s", request.method, request.url)
        logger.info("Headers: %s", dict(request.headers))
        logger.info("Body: %s", request.get_data())

@app.after_request
def log_response_info(response):
    if VERBOSE_LOGGING:
        logger.info("=== Outgoing Response ===")
        logger.info("Status: %s", response.status)
        logger.info("Headers: %s", dict(response.headers))
        logger.info("Body: %s", response.get_data())
    return response

@app.route('/traefik-config', methods=['GET'])
def get_traefik_config():
    """
    Returns the dynamic configuration for Traefik by querying the Kubernetes API.
    It looks for ConfigMaps labeled with 'traefik-config-fragment=true' in the 'traefik'
    namespace (or the namespace specified by the CONFIG_NAMESPACE env var), merges them, 
    and outputs the combined config as YAML.
    """
    namespace = os.getenv("CONFIG_NAMESPACE", "traefik")
    logger.info("Loading configuration fragments from the Kubernetes API in namespace: %s", namespace)
    config_data = load_configs_from_api(namespace=namespace)
    config_yaml = yaml.dump(config_data, default_flow_style=False)
    return Response(config_yaml, mimetype='text/plain')

@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200

@app.route('/version', methods=['GET'])
def version():
    VERSION = os.getenv("CONFIG_SERVICE_VERSION", "unknown")
    return jsonify({"version": VERSION}), 200

def main():
    parser = argparse.ArgumentParser(
        description="HTTP service to provide Traefik dynamic configuration via Kubernetes API"
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help="Enable full logging of every request/response to stdout"
    )
    parser.add_argument(
        '--port', type=int, default=5000,
        help="Port on which the config service will listen (default: 5000)"
    )
    args = parser.parse_args()

    global VERBOSE_LOGGING
    VERBOSE_LOGGING = args.verbose

    if VERBOSE_LOGGING:
        logger.setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled.")

    app.run(host="0.0.0.0", port=args.port)

if __name__ == '__main__':
    main()
