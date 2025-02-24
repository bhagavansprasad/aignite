#!/bin/bash

# Define directories to be created
dirs=(
    "./tests/test_db_manager"
    "./tests/test_ai"
    "./tests/test_models"
    "./tests/test_api"
    "./tests/test_services"
    "./logs"
    "./scripts"
    "./app/static/reports"
    "./app/static/pdfs"
    "./app/static/images"
    "./app/media/recommendation_outputs"
    "./app/media/user_profiles"
    "./app/media/assessment_reports"
    "./app/api"
    "./app/database_drivers"
    "./app/core"
    "./app/ai/models"
    "./app/ai/llm_connectors"
    "./app/ai/schemas"
    "./app/ai/services"
    "./app/ai/prompts"
    "./app/models"
    "./app/schemas"
    "./app/services"
    "./docs"
    "./docs/usecases"
    "./docs/prompts"
)

# Define files to be created
files=(
    "./requirements.txt"
    "./docker-compose.yml"
    "./db_manager.py"
    "./tests/test_ai/test_difficulty.py"
    "./tests/test_ai/test_recommendation.py"
    "./tests/conftest.py"
    "./tests/test_models/test_user.py"
    "./tests/test_models/test_course.py"
    "./tests/test_models/test_assessment.py"
    "./tests/test_api/test_recommendations.py"
    "./tests/test_api/test_assessments.py"
    "./tests/test_api/test_ai_engine.py"
    "./tests/test_api/test_users.py"
    "./tests/test_api/test_courses.py"
    "./tests/test_services/test_course_service.py"
    "./tests/test_services/test_user_service.py"
    "./tests/test_services/test_ai_service.py"
    "./tests/test_db_manager.py"
    "./tests/__init__.py"
    "./scripts/start_celery.sh"
    "./scripts/setup_env.sh"
    "./scripts/generate_test_data.py"
    "./scripts/db_init.py"
    "./scripts/backup_db.sh"
    "./README.md"
    "./Makefile"
    "./app/static/__init__.py"
    "./app/media/__init__.py"
    "./app/api/__init__.py"
    "./app/database_drivers/mongo_driver.py"
    "./app/database_drivers/mysql_driver.py"
    "./app/database_drivers/postgres_driver.py"
    "./app/database_drivers/base_driver.py"
    "./app/database_drivers/sqlite_driver.py"
    "./app/database_drivers/__init__.py"
    "./app/core/security.py"
    "./app/core/database.py"
    "./app/core/logging_config.py"
    "./app/core/utils.py"
    "./app/core/__init__.py"
    "./app/core/async_tasks.py"
    "./app/core/config.py"
    "./app/core/cache_manager.py"
    "./app/ai/models/qa_response_model.py"
    "./app/ai/models/prompt_model.py"
    "./app/ai/models/llm_response_model.py"
    "./app/ai/models/__init__.py"
    "./app/ai/recommendation.py"
    "./app/ai/difficulty.py"
    "./app/ai/llm_connectors/cohere_connector.py"
    "./app/ai/llm_connectors/huggingface_connector.py"
    "./app/ai/llm_connectors/openai_connector.py"
    "./app/ai/llm_connectors/__init__.py"
    "./app/ai/schemas/qa_response_schema.py"
    "./app/ai/schemas/prompt_schema.py"
    "./app/ai/schemas/llm_response_schema.py"
    "./app/ai/schemas/__init__.py"
    "./app/ai/__init__.py"
    "./app/ai/services/recommendation_service.py"
    "./app/ai/services/difficulty_service.py"
    "./app/ai/services/__init__.py"
    "./app/ai/ai_service.py"
    "./app/ai/prompts/recommend_topic_prompt.txt"
    "./app/ai/prompts/__init__.py"
    "./app/ai/prompts/generate_assessment_prompt.txt"
    "./app/models/user.py"
    "./app/models/course.py"
    "./app/models/recommendation.py"
    "./app/models/learning_progress.py"
    "./app/models/__init__.py"
    "./app/models/base.py"
    "./app/models/assessment.py"
    "./app/main.py"
    "./app/schemas/learning_progress_schemas.py"
    "./app/schemas/user_schemas.py"
    "./app/schemas/recommendation_schemas.py"
    "./app/schemas/assessment_schemas.py"
    "./app/schemas/__init__.py"
    "./app/schemas/course_schemas.py"
    "./app/__init__.py"
    "./app/services/course_service.py"
    "./app/services/assessment_service.py"
    "./app/services/recommendation_service.py"
    "./app/services/__init__.py"
    "./app/services/user_service.py"
    "./app/services/learning_progress_service.py"
    "./docs/aignite-ppt.txt"
    "./docs/source-tree-create-shscript.sh"
    "./docs/database_schema.md"
    "./docs/setup_guide.md"
    "./docs/api_endpoints.md"
    "./docs/ai_models.md"
    "./docs/swagger_generated.json"
    "./docs/01-phases.txt"
    "./docs/usecases/01-KnowledgeBase-AI-Chatbot.puml"
    "./docs/usecases/usecase-list.md"
    "./docs/prompts/02-framework-source-tree.prompt"
)

# Create directories
for dir in "${dirs[@]}"; do
    mkdir -p "$dir"
    echo "Created directory: $dir"
done

# Create empty files
for file in "${files[@]}"; do
    touch "$file"
    echo "Created file: $file"
done

echo "Folder tree and files setup completed."
