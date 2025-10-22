#!/usr/bin/env python3
"""
Command-line interface for the Training Job Orchestrator.
"""

import click
import requests
import json
from typing import Optional
from datetime import datetime
from tabulate import tabulate
import sys

# API configuration
API_BASE_URL = "http://localhost:8080"


class OrchestratorAPI:
    """API client wrapper"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def _request(self, method: str, endpoint: str, **kwargs):
        """Make API request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    def get_jobs(self, status: Optional[str] = None):
        """Get all jobs"""
        params = {"status": status} if status else {}
        return self._request("GET", "/jobs", params=params)
    
    def get_job(self, job_id: str):
        """Get specific job"""
        return self._request("GET", f"/jobs/{job_id}")
    
    def create_job(self, job_data: dict):
        """Create new job"""
        return self._request("POST", "/jobs", json=job_data)
    
    def delete_job(self, job_id: str):
        """Delete job"""
        return self._request("DELETE", f"/jobs/{job_id}")
    
    def retry_job(self, job_id: str):
        """Retry failed job"""
        return self._request("POST", f"/jobs/{job_id}/retry")
    
    def get_stats(self):
        """Get statistics"""
        return self._request("GET", "/stats")
    
    def health_check(self):
        """Check API health"""
        return self._request("GET", "/health")


@click.group()
@click.option('--api-url', default=API_BASE_URL, help='API base URL')
@click.pass_context
def cli(ctx, api_url):
    """Training Job Orchestrator CLI"""
    ctx.ensure_object(dict)
    ctx.obj['api'] = OrchestratorAPI(api_url)


@cli.command()
@click.option('--status', type=click.Choice(['pending', 'running', 'completed', 'failed', 'retrying']), 
              help='Filter by status')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
@click.pass_context
def list(ctx, status, output_format):
    """List all training jobs"""
    api = ctx.obj['api']
    result = api.get_jobs(status=status)
    
    if output_format == 'json':
        click.echo(json.dumps(result, indent=2))
        return
    
    if not result['jobs']:
        click.echo("No jobs found.")
        return
    
    # Format as table
    headers = ['Job ID', 'Name', 'Status', 'Retries', 'Started', 'Completed']
    rows = []
    
    for job in result['jobs']:
        rows.append([
            job['job_id'][:12],
            job['name'][:30],
            job['status'],
            f"{job['retry_count']}/{job['max_retries']}",
            job.get('started_at', 'N/A')[:19] if job.get('started_at') else 'N/A',
            job.get('completed_at', 'N/A')[:19] if job.get('completed_at') else 'N/A'
        ])
    
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    click.echo(f"\nTotal: {result['total']} jobs")


@cli.command()
@click.argument('job_id')
@click.pass_context
def get(ctx, job_id):
    """Get details of a specific job"""
    api = ctx.obj['api']
    job = api.get_job(job_id)
    
    click.echo("\n" + "=" * 60)
    click.echo(f"Job Details: {job['name']}")
    click.echo("=" * 60)
    click.echo(f"Job ID:        {job['job_id']}")
    click.echo(f"Status:        {job['status']}")
    click.echo(f"Retry Count:   {job['retry_count']}/{job['max_retries']}")
    click.echo(f"Started At:    {job.get('started_at', 'N/A')}")
    click.echo(f"Completed At:  {job.get('completed_at', 'N/A')}")
    
    if job.get('error_message'):
        click.echo(f"\nError Message:\n{job['error_message']}")
    
    click.echo("=" * 60 + "\n")


@cli.command()
@click.option('--name', required=True, help='Job name')
@click.option('--image', required=True, help='Docker image')
@click.option('--command', required=True, multiple=True, help='Command to run (can specify multiple times)')
@click.option('--schedule', required=True, help='Cron schedule')
@click.option('--max-retries', default=3, help='Maximum retry attempts')
@click.option('--checkpoint-path', help='Path for checkpoints')
@click.pass_context
def create(ctx, name, image, command, schedule, max_retries, checkpoint_path):
    """Create a new training job"""
    api = ctx.obj['api']
    
    job_data = {
        "name": name,
        "image": image,
        "command": list(command),
        "schedule": schedule,
        "max_retries": max_retries
    }
    
    if checkpoint_path:
        job_data["checkpoint_path"] = checkpoint_path
    
    click.echo("Creating job...")
    result = api.create_job(job_data)
    
    click.echo(f"\n✓ Job created successfully!")
    click.echo(f"Job ID: {result['job_id']}")
    click.echo(f"Status: {result['status']}")


@cli.command()
@click.argument('job_id')
@click.confirmation_option(prompt='Are you sure you want to delete this job?')
@click.pass_context
def delete(ctx, job_id):
    """Delete a training job"""
    api = ctx.obj['api']
    result = api.delete_job(job_id)
    click.echo(f"✓ {result['message']}")


@cli.command()
@click.argument('job_id')
@click.pass_context
def retry(ctx, job_id):
    """Manually retry a failed job"""
    api = ctx.obj['api']
    result = api.retry_job(job_id)
    click.echo(f"✓ {result['message']}")


@cli.command()
@click.pass_context
def stats(ctx):
    """Show orchestrator statistics"""
    api = ctx.obj['api']
    stats = api.get_stats()
    
    click.echo("\n" + "=" * 40)
    click.echo("Training Job Statistics")
    click.echo("=" * 40)
    click.echo(f"Total Jobs:    {stats['total_jobs']}")
    click.echo(f"Pending:       {stats['pending']}")
    click.echo(f"Running:       {stats['running']}")
    click.echo(f"Completed:     {stats['completed']}")
    click.echo(f"Failed:        {stats['failed']}")
    click.echo(f"Retrying:      {stats['retrying']}")
    
    if stats['total_jobs'] > 0:
        success_rate = (stats['completed'] / stats['total_jobs']) * 100
        click.echo(f"\nSuccess Rate:  {success_rate:.1f}%")
    
    click.echo("=" * 40 + "\n")


@cli.command()
@click.pass_context
def health(ctx):
    """Check orchestrator health"""
    api = ctx.obj['api']
    
    try:
        result = api.health_check()
        click.echo(f"✓ Orchestrator is healthy")
        click.echo(f"Status: {result['status']}")
        click.echo(f"Timestamp: {result['timestamp']}")
    except Exception as e:
        click.echo(f"✗ Orchestrator is unhealthy: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--job-id', help='Filter logs for specific job')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.pass_context
def logs(ctx, job_id, follow):
    """View orchestrator logs (requires kubectl access)"""
    import subprocess
    
    namespace = "training"
    cmd = ["kubectl", "logs", "-n", namespace, "-l", "app=training-orchestrator"]
    
    if follow:
        cmd.append("-f")
    
    if job_id:
        cmd.extend(["--grep", job_id])
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        click.echo(f"Error accessing logs: {e}", err=True)


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def failed(ctx, output_format):
    """List all failed jobs"""
    api = ctx.obj['api']
    result = api.get_jobs(status='failed')
    
    if output_format == 'json':
        click.echo(json.dumps(result, indent=2))
        return
    
    if not result['jobs']:
        click.echo("No failed jobs found.")
        return
    
    headers = ['Job ID', 'Name', 'Retries', 'Error', 'Failed At']
    rows = []
    
    for job in result['jobs']:
        error = job.get('error_message', 'N/A')
        if len(error) > 50:
            error = error[:47] + '...'
        
        rows.append([
            job['job_id'][:12],
            job['name'][:30],
            f"{job['retry_count']}/{job['max_retries']}",
            error,
            job.get('completed_at', 'N/A')[:19] if job.get('completed_at') else 'N/A'
        ])
    
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    click.echo(f"\nTotal failed jobs: {len(result['jobs'])}")


@cli.command()
@click.pass_context
def running(ctx):
    """List all currently running jobs"""
    api = ctx.obj['api']
    result = api.get_jobs(status='running')
    
    if not result['jobs']:
        click.echo("No running jobs.")
        return
    
    headers = ['Job ID', 'Name', 'Started', 'Duration']
    rows = []
    
    for job in result['jobs']:
        started = job.get('started_at')
        if started:
            start_time = datetime.fromisoformat(started.replace('Z', '+00:00'))
            duration = datetime.now().astimezone() - start_time
            duration_str = str(duration).split('.')[0]  # Remove microseconds
        else:
            duration_str = 'N/A'
        
        rows.append([
            job['job_id'][:12],
            job['name'][:30],
            started[:19] if started else 'N/A',
            duration_str
        ])
    
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@cli.command()
@click.option('--watch', '-w', is_flag=True, help='Continuously watch status')
@click.option('--interval', default=5, help='Refresh interval in seconds')
@click.pass_context
def watch(ctx, watch, interval):
    """Watch job status in real-time"""
    import time
    import os
    
    api = ctx.obj['api']
    
    try:
        while True:
            # Clear screen
            os.system('clear' if os.name == 'posix' else 'cls')
            
            # Get stats
            stats = api.get_stats()
            
            click.echo("=" * 60)
            click.echo(f"Training Job Orchestrator - Live Status")
            click.echo(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo("=" * 60)
            
            # Display stats
            click.echo(f"\nTotal:     {stats['total_jobs']}")
            click.echo(f"Pending:   {stats['pending']}")
            click.echo(f"Running:   {stats['running']}")
            click.echo(f"Completed: {stats['completed']}")
            click.echo(f"Failed:    {stats['failed']}")
            
            # Display running jobs
            running = api.get_jobs(status='running')
            if running['jobs']:
                click.echo(f"\n--- Running Jobs ({len(running['jobs'])}) ---")
                for job in running['jobs']:
                    click.echo(f"  • {job['name']} ({job['job_id'][:8]}...)")
            
            if not watch:
                break
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        click.echo("\n\nStopped watching.")


@cli.group()
def config():
    """Configuration management"""
    pass


@config.command('show')
@click.pass_context
def config_show(ctx):
    """Show current configuration"""
    api = ctx.obj['api']
    click.echo(f"\nAPI URL: {api.base_url}")
    
    try:
        health = api.health_check()
        click.echo(f"Status: Connected ✓")
    except:
        click.echo(f"Status: Disconnected ✗")


@config.command('set-url')
@click.argument('url')
@click.pass_context
def config_set_url(ctx, url):
    """Set API URL"""
    # In a real implementation, save this to a config file
    click.echo(f"API URL set to: {url}")
    click.echo("Note: Use --api-url flag to specify URL per command")


@cli.group()
def job():
    """Job template management"""
    pass


@job.command('template')
@click.option('--name', default='my-training-job', help='Job name')
def job_template(name):
    """Generate a job template"""
    template = {
        "name": name,
        "image": "your-registry/trainer:latest",
        "command": ["python", "train.py", "--epochs", "10"],
        "schedule": "0 2 * * *",
        "max_retries": 3,
        "checkpoint_path": f"/checkpoints/{name}"
    }
    
    click.echo("\n# Training Job Template")
    click.echo("# Modify and use with: orchestrator-cli create --from-file job.json\n")
    click.echo(json.dumps(template, indent=2))


@job.command('validate')
@click.argument('job_file', type=click.File('r'))
def job_validate(job_file):
    """Validate a job configuration file"""
    try:
        job_data = json.load(job_file)
        
        required_fields = ['name', 'image', 'command', 'schedule']
        missing = [f for f in required_fields if f not in job_data]
        
        if missing:
            click.echo(f"✗ Missing required fields: {', '.join(missing)}", err=True)
            sys.exit(1)
        
        # Validate cron schedule
        from croniter import croniter
        try:
            croniter(job_data['schedule'])
        except:
            click.echo(f"✗ Invalid cron schedule: {job_data['schedule']}", err=True)
            sys.exit(1)
        
        click.echo("✓ Job configuration is valid")
        
    except json.JSONDecodeError as e:
        click.echo(f"✗ Invalid JSON: {e}", err=True)
        sys.exit(1)


@cli.command('export')
@click.argument('output_file', type=click.File('w'))
@click.pass_context
def export(ctx, output_file):
    """Export all jobs to a file"""
    api = ctx.obj['api']
    result = api.get_jobs()
    
    json.dump(result, output_file, indent=2)
    click.echo(f"✓ Exported {result['total']} jobs to {output_file.name}")


@cli.command('import')
@click.argument('input_file', type=click.File('r'))
@click.option('--dry-run', is_flag=True, help='Validate without creating')
@click.pass_context
def import_jobs(ctx, input_file, dry_run):
    """Import jobs from a file"""
    api = ctx.obj['api']
    
    try:
        data = json.load(input_file)
        jobs = data.get('jobs', [])
        
        if dry_run:
            click.echo(f"Would import {len(jobs)} jobs:")
            for job in jobs:
                click.echo(f"  • {job['name']}")
            return
        
        created = 0
        for job in jobs:
            try:
                api.create_job(job)
                created += 1
                click.echo(f"✓ Created: {job['name']}")
            except Exception as e:
                click.echo(f"✗ Failed to create {job['name']}: {e}", err=True)
        
        click.echo(f"\n✓ Successfully imported {created}/{len(jobs)} jobs")
        
    except json.JSONDecodeError as e:
        click.echo(f"✗ Invalid JSON file: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli(obj={})