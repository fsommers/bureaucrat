#!/usr/bin/env python3
"""
Check and verify the AI provider abstraction layer configuration.

This script helps verify that the provider system is correctly configured
and working with your chosen AI provider (Gemini, Hugging Face, etc.).
"""

import click
from ai_providers import get_ai_client, ProviderFactory


@click.command()
@click.option('--provider', '-p', default='gemini', help='AI provider to check (gemini/huggingface)')
@click.option('--test-generation', is_flag=True, help='Test entity generation')
@click.option('--test-vision', is_flag=True, help='Test vision capabilities')
def check_providers(provider, test_generation, test_vision):
    """Check and verify the AI provider configuration."""

    click.echo(f"🧪 Testing AI Provider System with: {provider}")
    click.echo("-" * 50)

    # List available providers
    available = ProviderFactory.list_providers()
    click.echo(f"📋 Available providers: {', '.join(available)}")

    try:
        # Get the AI client
        click.echo(f"\n🔧 Initializing {provider} provider...")
        client = get_ai_client(provider=provider)
        click.echo(f"✅ Successfully initialized {client.get_provider_name()} provider")

        # Get model info
        model_info = client.get_model_info()
        click.echo(f"\n📊 Model Information:")
        for key, value in model_info.items():
            click.echo(f"  - {key}: {value}")

        # Test entity generation if requested
        if test_generation:
            click.echo(f"\n🎯 Testing entity generation...")
            try:
                entities = client.generate_bulk_entity_data(
                    document_type="test invoice",
                    entity_fields=["customer_name", "amount"],
                    count=2,
                    language="en"
                )
                click.echo(f"✅ Successfully generated {len(entities)} entities")
                click.echo(f"📝 Sample entity: {entities[0] if entities else 'None'}")
            except Exception as e:
                click.echo(f"❌ Entity generation failed: {e}")

        # Test vision capabilities if requested
        if test_vision:
            if client.supports_vision():
                click.echo(f"\n👁️ Provider supports vision capabilities")
                click.echo("  (Actual vision test requires an image file)")
            else:
                click.echo(f"\n⚠️  Provider does not support vision capabilities")

        click.echo(f"\n✅ Provider system test completed successfully!")

    except ValueError as e:
        click.echo(f"❌ Configuration Error: {e}")
        click.echo("\n💡 Make sure you have set up your .env file with the required API keys:")
        if provider == 'gemini':
            click.echo("  GEMINI_API_KEY=your_api_key_here")
        elif provider == 'huggingface':
            click.echo("  HUGGINGFACE_API_KEY=your_api_key_here")

    except Exception as e:
        click.echo(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    check_providers()