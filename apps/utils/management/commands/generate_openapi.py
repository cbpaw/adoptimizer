import os
import yaml
from django.core.management.base import BaseCommand
from django.conf import settings
from django.test import RequestFactory
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.generators import SchemaGenerator


class Command(BaseCommand):
    help = "Generate OpenAPI schema as a YAML file for API documentation and Postman import"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            default="openapi.yaml",
            help="Output file path (default: openapi.yaml)",
        )
        parser.add_argument(
            "--format",
            "-f",
            type=str,
            choices=["yaml", "json"],
            default="yaml",
            help="Output format (default: yaml)",
        )
        parser.add_argument(
            "--title",
            "-t",
            type=str,
            help="API title (overrides settings)",
        )
        parser.add_argument(
            "--api-version",
            type=str,
            help="API version (overrides settings)",
        )
        parser.add_argument(
            "--description",
            "-d",
            type=str,
            help="API description (overrides settings)",
        )

    def handle(self, *args, **options):
        """Generate OpenAPI schema and write to file."""
        self.stdout.write("Generating OpenAPI schema...")

        # Create schema generator
        generator = SchemaGenerator(
            title=options.get("title") or getattr(settings, "SPECTACULAR_SETTINGS", {}).get("TITLE", "AdOptimizer API"),
            description=options.get("description") or getattr(settings, "SPECTACULAR_SETTINGS", {}).get("DESCRIPTION", "AdOptimizer API Documentation"),
            version=options.get("api_version") or getattr(settings, "SPECTACULAR_SETTINGS", {}).get("VERSION", "1.0.0"),
        )

        # Generate the schema
        schema = generator.get_schema(request=None, public=True)

        # Prepare output file path
        output_file = options["output"]
        if not os.path.isabs(output_file):
            output_file = os.path.join(settings.BASE_DIR, output_file)

        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Write schema to file
        try:
            if options["format"] == "yaml":
                with open(output_file, "w", encoding="utf-8") as f:
                    yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ OpenAPI schema generated successfully: {output_file}")
                )
            else:  # json
                import json
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(schema, f, indent=2, ensure_ascii=False)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ OpenAPI schema generated successfully: {output_file}")
                )

            # Print some statistics
            paths_count = len(schema.get("paths", {}))
            components_count = len(schema.get("components", {}).get("schemas", {}))

            self.stdout.write(f"📊 Schema Statistics:")
            self.stdout.write(f"   • API Endpoints: {paths_count}")
            self.stdout.write(f"   • Component Schemas: {components_count}")

            # Print import instructions
            self.stdout.write(f"\n🚀 Usage Instructions:")
            self.stdout.write(f"   • Postman: Import → Link → Upload Files → Select {output_file}")
            self.stdout.write(f"   • Insomnia: Import Data → From File → Select {output_file}")
            self.stdout.write(f"   • SwaggerUI: Upload file to https://editor.swagger.io/")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error writing schema to file: {e}")
            )
            raise

        self.stdout.write(
            self.style.SUCCESS("\n🎉 OpenAPI generation completed successfully!")
        )