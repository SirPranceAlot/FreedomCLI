"""Model fetching, selection, pricing, and recommendations."""

# Standard library imports
import time

# Third-party imports
import requests
from rich.prompt import Prompt

# Local imports
from freedomcli.constants import console
from freedomcli.config import load_config


def get_available_models():
    """Fetch available models from OpenRouter API"""
    try:
        config = load_config()
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }

        with console.status("[bold green]Fetching available models..."):
            response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)

        if response.status_code == 200:
            models_data = response.json()
            return models_data["data"]
        console.print(f"[red]Error fetching models: {response.status_code}[/red]")
        return []
    except Exception as e:
        console.print(f"[red]Error fetching models: {str(e)}[/red]")
        return []


def get_model_info(model_id):
    """Get model information of all models"""
    models = get_available_models()
    
    try:
        for model in models:
            if model["id"] == model_id:
                return model
        
        console.print(f"[yellow]Warning: Could not find info for model '{model_id}'.[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red] Failed to fetch model info: {str(e)}[/red]")
        return None


def get_enhanced_models():
    """Fetch enhanced model data from OpenRouter frontend API with detailed capabilities"""
    try:
        config = load_config()
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }

        with console.status("[bold green]Fetching enhanced model data..."):
            response = requests.get("https://openrouter.ai/api/frontend/models", headers=headers)

        if response.status_code == 200:
            models_data = response.json()
            return models_data.get("data", [])
        else:
            console.print(f"[red]Error fetching enhanced models: {response.status_code}[/red]")
            # Fallback to standard models API
            return get_available_models()
    except Exception as e:
        console.print(f"[red]Error fetching enhanced models: {str(e)}[/red]")
        # Fallback to standard models API
        return get_available_models()


def get_models_by_capability(capability_filter="all"):
    """Get models filtered by specific capabilities using the enhanced frontend API"""
    try:
        enhanced_models = get_enhanced_models()
        
        if capability_filter == "all":
            return enhanced_models
        
        filtered_models = []
        
        for model in enhanced_models:
            # Skip None models
            if model is None:
                continue
                
            # Extract capability information from the endpoint data
            endpoint = model.get('endpoint', {})
            if endpoint is None:
                continue
            
            if capability_filter == "reasoning":
                # Check if model supports reasoning/thinking
                supports_reasoning = endpoint.get('supports_reasoning', False)
                reasoning_config = model.get('reasoning_config') or endpoint.get('reasoning_config')
                if supports_reasoning or reasoning_config:
                    filtered_models.append(model)
                    
            elif capability_filter == "multipart":
                # Check if model supports multipart (images/files)
                supports_multipart = endpoint.get('supports_multipart', False)
                input_modalities = model.get('input_modalities', [])
                if supports_multipart or ('image' in input_modalities):
                    filtered_models.append(model)
                    
            elif capability_filter == "tools":
                # Check if model supports tool parameters
                supports_tools = endpoint.get('supports_tool_parameters', False)
                supported_params = endpoint.get('supported_parameters', [])
                if supported_params is None:
                    supported_params = []
                if supports_tools or 'tools' in supported_params:
                    filtered_models.append(model)
                    
            elif capability_filter == "free":
                # Check if model is free
                is_free = endpoint.get('is_free', False)
                pricing = endpoint.get('pricing', {})
                if pricing is None:
                    pricing = {}
                prompt_price = float(pricing.get('prompt', '0'))
                if is_free or prompt_price == 0:
                    filtered_models.append(model)
                    
        return filtered_models
        
    except Exception as e:
        console.print(f"[red]Error filtering models by capability: {str(e)}[/red]")
        # Fallback to standard models
        return get_available_models()


def get_models_by_group():
    """Get models organized by their groups using enhanced API"""
    try:
        enhanced_models = get_enhanced_models()
        groups = {}
        
        for model in enhanced_models:
            # Skip None models
            if model is None:
                continue
                
            group = model.get('group', 'Other')
            if group not in groups:
                groups[group] = []
            groups[group].append(model)
        
        return groups
        
    except Exception as e:
        console.print(f"[red]Error grouping models: {str(e)}[/red]")
        return {}


def get_models_by_provider():
    """Get models organized by their providers using enhanced API"""
    try:
        enhanced_models = get_enhanced_models()
        providers = {}
        
        for model in enhanced_models:
            # Skip None models
            if model is None:
                continue
                
            endpoint = model.get('endpoint', {})
            if endpoint is None:
                continue
                
            provider = endpoint.get('provider_name', 'Unknown')
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(model)
        
        return providers
        
    except Exception as e:
        console.print(f"[red]Error organizing models by provider: {str(e)}[/red]")
        return {}


def get_models_by_categories(categories):
    """Fetch models by categories from OpenRouter API using the find endpoint"""
    try:
        config = load_config()
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }

        # Convert categories list to comma-separated string for the API
        categories_param = ",".join(categories) if isinstance(categories, list) else categories
        
        with console.status(f"[bold green]Fetching models for categories: {categories_param}..."):
            response = requests.get(
                f"https://openrouter.ai/api/frontend/models/find?categories={categories_param}",
                headers=headers
            )

        if response.status_code == 200:
            models_data = response.json()
            # Extract model slugs from the response
            if "data" in models_data and "models" in models_data["data"]:
                return [model["slug"] for model in models_data["data"]["models"]]
            return []
        else:
            console.print(f"[red]Error fetching models by categories: {response.status_code}[/red]")
            return []
    except Exception as e:
        console.print(f"[red]Error fetching models by categories: {str(e)}[/red]")
        return []


def get_dynamic_task_categories():
    """Get dynamic task categories by fetching models from specific OpenRouter categories"""
    # Map our task types to OpenRouter categories and fallback model patterns
    category_mapping = {
        "creative": {
            "openrouter_categories": ["Programming", "Technology"],
            "fallback_patterns": ["claude-3", "gpt-4", "llama", "gemini"]
        },
        "coding": {
            "openrouter_categories": ["Programming", "Technology"],
            "fallback_patterns": ["claude-3-opus", "gpt-4", "deepseek-coder", "qwen-coder", "devstral", "codestral"]
        },
        "analysis": {
            "openrouter_categories": ["Science", "Academia"],
            "fallback_patterns": ["claude-3-opus", "gpt-4", "mistral", "qwen"]
        },
        "chat": {
            "openrouter_categories": ["Programming"],
            "fallback_patterns": ["claude-3-haiku", "gpt-3.5", "gemini-pro", "llama"]
        }
    }

    dynamic_categories = {}
    
    for task_type, config in category_mapping.items():
        try:
            # Try to get models from OpenRouter categories first
            category_models = get_models_by_categories(config["openrouter_categories"])
            
            if category_models:
                # Filter to get relevant models based on fallback patterns for better accuracy
                filtered_models = []
                for model_slug in category_models:
                    if any(pattern in model_slug.lower() for pattern in config["fallback_patterns"]):
                        filtered_models.append(model_slug)
                
                # If we found filtered models, use them, otherwise use all category models
                dynamic_categories[task_type] = filtered_models if filtered_models else category_models[:10]
            else:
                # Fallback to pattern-based filtering with all available models
                all_models = get_available_models()
                fallback_models = []
                for model in all_models:
                    model_id = model.get('id', '').lower()
                    if any(pattern in model_id for pattern in config["fallback_patterns"]):
                        fallback_models.append(model['id'])
                
                dynamic_categories[task_type] = fallback_models[:10]
                        
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to get dynamic categories for {task_type}: {str(e)}[/yellow]")
            # Use fallback patterns in case of error
            dynamic_categories[task_type] = config["fallback_patterns"]
    
    return dynamic_categories


def auto_detect_thinking_mode(config, selected_model):
    """Automatically detect if the selected model supports thinking mode"""
    # Make sure the thinking_mode key exists in config
    if 'thinking_mode' not in config:
        config['thinking_mode'] = False  # Default to disabled

    try:
        # Get enhanced models to check if this model supports reasoning
        enhanced_models = get_enhanced_models()
        
        for model in enhanced_models:
            if model is None:
                continue
                
            # Check if this is the selected model
            model_slug = model.get('slug') or model.get('name') or model.get('short_name', '')
            if model_slug == selected_model:
                # Check if model supports reasoning/thinking
                endpoint = model.get('endpoint', {})
                supports_reasoning = endpoint.get('supports_reasoning', False) if endpoint else False
                reasoning_config = model.get('reasoning_config') or (endpoint.get('reasoning_config') if endpoint else None)
                
                if supports_reasoning or reasoning_config:
                    config['thinking_mode'] = True
                    console.print("[green]🧠 Thinking mode automatically enabled for this reasoning model.[/green]")
                    if reasoning_config:
                        start_token = reasoning_config.get('start_token', '<thinking>')
                        end_token = reasoning_config.get('end_token', '</thinking>')
                        console.print(f"[dim]Uses reasoning tags: {start_token}...{end_token}[/dim]")
                else:
                    config['thinking_mode'] = False
                    console.print("[dim]Thinking mode disabled - this model doesn't support reasoning.[/dim]")
                return
        
        # If model not found in enhanced models, disable thinking mode
        config['thinking_mode'] = False
        console.print("[dim]Thinking mode disabled - unable to verify reasoning support.[/dim]")
        
    except Exception as e:
        # If there's an error, keep current setting or default to disabled
        config['thinking_mode'] = config.get('thinking_mode', False)
        console.print(f"[yellow]Could not auto-detect thinking mode: {str(e)}[/yellow]")
        console.print(f"[dim]Keeping current setting: {'enabled' if config['thinking_mode'] else 'disabled'}[/dim]")


def get_model_pricing_info(model_name):
    """Get pricing information for a specific model"""
    try:
        enhanced_models = get_enhanced_models()
        
        for model in enhanced_models:
            if model is None:
                continue
                
            # Check if this is the selected model
            model_slug = model.get('slug') or model.get('name') or model.get('short_name', '')
            if model_slug == model_name:
                endpoint = model.get('endpoint', {})
                if endpoint:
                    api_is_free = endpoint.get('is_free', False)
                    pricing = endpoint.get('pricing', {})
                    
                    # Check if the model name explicitly indicates it's free
                    is_explicitly_free = model_name and (model_name.endswith(':free') or ':free' in model_name)
                    
                    # For explicitly free models, always return free pricing regardless of API data
                    if is_explicitly_free:
                        return {
                            'is_free': True,
                            'prompt_price': 0.0,
                            'completion_price': 0.0,
                            'display': 'FREE (OpenRouter)',
                            'provider': endpoint.get('provider_name', 'Unknown')
                        }
                    elif pricing:
                        prompt_price = float(pricing.get('prompt', '0'))
                        completion_price = float(pricing.get('completion', '0'))
                        
                        if prompt_price == 0 and completion_price == 0:
                            # Model has 0 pricing but may still require credits
                            # Don't trust 0-pricing for non-explicit free models
                            return {
                                'is_free': False,
                                'prompt_price': 0.0,
                                'completion_price': 0.0,
                                'display': 'Requires credits',
                                'provider': endpoint.get('provider_name', 'Unknown')
                            }
                        else:
                            # Format prices for display
                            if prompt_price * 1000 < 0.001:
                                prompt_display = f"${prompt_price * 1000:.4f}"
                            else:
                                prompt_display = f"${prompt_price * 1000:.3f}"
                                
                            if completion_price * 1000 < 0.001:
                                completion_display = f"${completion_price * 1000:.4f}"
                            else:
                                completion_display = f"${completion_price * 1000:.3f}"
                                
                            return {
                                'is_free': False,
                                'prompt_price': prompt_price,
                                'completion_price': completion_price,
                                'display': f"{prompt_display}/1K prompt, {completion_display}/1K completion",
                                'provider': endpoint.get('provider_name', 'Unknown')
                            }
        
        # Model not found in enhanced models - check if it's a free model by name
        if model_name and (model_name.endswith(':free') or ':free' in model_name):
            return {
                'is_free': True,
                'prompt_price': 0.0,
                'completion_price': 0.0,
                'display': 'FREE',
                'provider': 'OpenRouter'
            }
        
        # Model not found in enhanced models and not obviously free
        return {
            'is_free': False,
            'prompt_price': 0.0,
            'completion_price': 0.0,
            'display': 'Pricing unknown - may require credits',
            'provider': 'Unknown'
        }
        
    except Exception as e:
        return {
            'is_free': False,
            'prompt_price': 0.0,
            'completion_price': 0.0,
            'display': 'Pricing unknown - may require credits',
            'provider': 'Unknown'
        }


def calculate_session_cost(total_prompt_tokens, total_completion_tokens, pricing_info):
    """Calculate the total cost for the current session"""
    if pricing_info['is_free']:
        return 0.0
    
    prompt_cost = total_prompt_tokens * pricing_info['prompt_price']
    completion_cost = total_completion_tokens * pricing_info['completion_price']
    
    return prompt_cost + completion_cost


def select_model(config):
    """Simplified model selection interface"""
    all_models = get_available_models()

    if not all_models:
        console.print("[red]No models available. Please check your API key and internet connection.[/red]")
        return None

    # Option to directly enter a model name
    console.print("[bold green]Model Selection[/bold green]")
    console.print("\n[bold magenta]Options:[/bold magenta]")
    console.print("[bold]1[/bold] - View all available models")
    console.print("[bold]2[/bold] - Show free models only")
    console.print("[bold]3[/bold] - Enter model name directly")
    console.print("[bold]4[/bold] - Browse models by task category")
    console.print("[bold]5[/bold] - Browse by capabilities (enhanced)")
    console.print("[bold]6[/bold] - Browse by model groups")
    console.print("[bold]q[/bold] - Cancel selection")

    choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6", "q"], default="1")

    if choice == "q":
        return None

    elif choice == "3":
        # Direct model name entry
        console.print("[yellow]Enter the exact model name (e.g., 'anthropic/claude-3-opus')[/yellow]")
        model_name = Prompt.ask("Model name")

        # Validate the model name
        model_exists = any(model["id"] == model_name for model in all_models)
        if model_exists:
            # Auto-detect thinking mode support first
            try:
                auto_detect_thinking_mode(config, model_name)
            except Exception as e:
                console.print(f"[yellow]Error auto-detecting thinking mode: {str(e)}. Using default settings.[/yellow]")
            return model_name

        console.print("[yellow]Warning: Model not found in available models. Using anyway.[/yellow]")
        confirm = Prompt.ask("Continue with this model name? (y/n)", default="y")
        if confirm.lower() == "y":
            # Auto-detect thinking mode support first
            try:
                auto_detect_thinking_mode(config, model_name)
            except Exception as e:
                console.print(f"[yellow]Error auto-detecting thinking mode: {str(e)}. Using default settings.[/yellow]")
            return model_name
        return select_model(config)  # Start over

    elif choice == "1":
        # All models, simple numbered list
        console.print("[bold green]All Available Models:[/bold green]")

        try:
            from pyfzf.pyfzf import FzfPrompt
            has_fzf = True
        except ImportError:
            has_fzf = False

        if has_fzf:
            try:
                fzf = FzfPrompt()
                model_choice = fzf.prompt([model['id'] for model in all_models])
                if not model_choice:
                    console.print("[red]No model selected. Exiting...[/red]")
                    return select_model(config)
                else:
                    try:
                        auto_detect_thinking_mode(config, model_choice[0])
                    except Exception as e:
                        console.print(f"[yellow]Error auto-detecting thinking mode: {str(e)}. Using default settings.[/yellow]")
                    return model_choice[0]
            except Exception as e:
                console.print(f"[yellow]FZF not available: {str(e)}. Falling back to numbered list.[/yellow]")

        with console.pager(styles=True):
            for i, model in enumerate(all_models, 1):
                # Highlight free models
                if model['id'].endswith(":free"):
                    console.print(f"[bold]{i}.[/bold] {model['id']} [green](FREE)[/green]")
                else:
                    console.print(f"[bold]{i}.[/bold] {model['id']}")

        model_choice = Prompt.ask("Enter model number or 'b' to go back", default="1")

        if model_choice.lower() == 'b':
            return select_model(config)

        try:
            index = int(model_choice) - 1
            if 0 <= index < len(all_models):
                selected_model = all_models[index]['id']
                # Auto-detect thinking mode support
                try:
                    auto_detect_thinking_mode(config, selected_model)
                except Exception as e:
                    console.print(f"[yellow]Error auto-detecting thinking mode: {str(e)}. Using default settings.[/yellow]")
                return selected_model
            else:
                console.print("[red]Invalid selection[/red]")
                return select_model(config)
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
            return select_model(config)

    elif choice == "2":
        # Show only free models
        free_models = [model for model in all_models if model['id'].endswith(":free")]

        if not free_models:
            console.print("[yellow]No free models found.[/yellow]")
            Prompt.ask("Press Enter to continue")
            return select_model(config)

        console.print("[bold green]Free Models:[/bold green]")
        for i, model in enumerate(free_models, 1):
            console.print(f"[bold]{i}.[/bold] {model['id']} [green](FREE)[/green]")

        model_choice = Prompt.ask("Enter model number or 'b' to go back", default="1")

        if model_choice.lower() == 'b':
            return select_model(config)

        try:
            index = int(model_choice) - 1
            if 0 <= index < len(free_models):
                selected_model = free_models[index]['id']
                # Auto-detect thinking mode support
                try:
                    auto_detect_thinking_mode(config, selected_model)
                except Exception as e:
                    console.print(f"[yellow]Error auto-detecting thinking mode: {str(e)}. Using default settings.[/yellow]")
                return selected_model
            console.print("[red]Invalid selection[/red]")
            Prompt.ask("Press Enter to continue")
            return select_model(config)
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
            Prompt.ask("Press Enter to continue")
            return select_model(config)

    elif choice == "4":
        # Browse models by task category using dynamic categories
        console.print("[bold green]Browse Models by Task Category:[/bold green]")
        console.print("[dim]Using dynamic categories from OpenRouter API[/dim]\n")
        
        # Available task categories
        task_categories = ["creative", "coding", "analysis", "chat"]
        
        console.print("[bold magenta]Available Categories:[/bold magenta]")
        for i, category in enumerate(task_categories, 1):
            console.print(f"[bold]{i}.[/bold] {category.title()}")
        console.print("[bold]b[/bold] - Go back to main menu")
        
        category_choice = Prompt.ask("Select a category", choices=["1", "2", "3", "4", "b"], default="1")
        
        if category_choice.lower() == 'b':
            return select_model(config)
        
        try:
            category_index = int(category_choice) - 1
            if 0 <= category_index < len(task_categories):
                selected_category = task_categories[category_index]
                
                # Get models for the selected category using dynamic categories
                console.print(f"[cyan]Loading {selected_category} models...[/cyan]")
                try:
                    dynamic_categories = get_dynamic_task_categories()
                    category_models = dynamic_categories.get(selected_category, [])
                    
                    if not category_models:
                        console.print(f"[yellow]No models found for {selected_category} category.[/yellow]")
                        Prompt.ask("Press Enter to continue")
                        return select_model(config)
                    
                    # Get full model details for display
                    all_models = get_available_models()
                    detailed_models = []
                    for model in all_models:
                        if model['id'] in category_models:
                            detailed_models.append(model)
                    
                    if not detailed_models:
                        console.print(f"[yellow]No detailed model information found for {selected_category} category.[/yellow]")
                        Prompt.ask("Press Enter to continue")
                        return select_model(config)
                    
                    console.print(f"[bold green]{selected_category.title()} Models:[/bold green]")
                    console.print(f"[dim]Found {len(detailed_models)} models optimized for {selected_category} tasks[/dim]\n")
                    
                    for i, model in enumerate(detailed_models, 1):
                        if model['id'].endswith(":free"):
                            console.print(f"[bold]{i}.[/bold] {model['id']} [green](FREE)[/green]")
                        else:
                            pricing = ""
                            if 'pricing' in model and 'prompt' in model['pricing']:
                                try:
                                    prompt_price = float(model['pricing']['prompt'])
                                    if prompt_price > 0:
                                        pricing = f" [dim](${prompt_price:.6f}/token)[/dim]"
                                except:
                                    pass
                            console.print(f"[bold]{i}.[/bold] {model['id']}{pricing}")
                    
                    console.print(f"\n[bold]b[/bold] - Go back to category selection")
                    
                    model_choice = Prompt.ask("Enter model number or 'b' to go back", default="1")
                    
                    if model_choice.lower() == 'b':
                        return select_model(config)
                    
                    try:
                        model_index = int(model_choice) - 1
                        if 0 <= model_index < len(detailed_models):
                            selected_model = detailed_models[model_index]['id']
                            console.print(f"[green]Selected {selected_model} for {selected_category} tasks[/green]")
                            
                            try:
                                auto_detect_thinking_mode(config, selected_model)
                            except Exception as e:
                                console.print(f"[yellow]Error auto-detecting thinking mode: {str(e)}. Using default settings.[/yellow]")
                            return selected_model
                        else:
                            console.print("[red]Invalid selection[/red]")
                            Prompt.ask("Press Enter to continue")
                            return select_model(config)
                    except ValueError:
                        console.print("[red]Please enter a valid number[/red]")
                        Prompt.ask("Press Enter to continue")
                        return select_model(config)
                        
                except Exception as e:
                    console.print(f"[red]Error loading dynamic categories: {str(e)}[/red]")
                    console.print("[yellow]Falling back to standard model selection[/yellow]")
                    Prompt.ask("Press Enter to continue")
                    return select_model(config)
            else:
                console.print("[red]Invalid category selection[/red]")
                return select_model(config)
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
            return select_model(config)

    elif choice == "5":
        # Browse models by capabilities using enhanced API
        console.print("[bold green]Browse Models by Capabilities:[/bold green]")
        console.print("[dim]Using enhanced OpenRouter frontend API data[/dim]\n")
        
        capabilities = [
            ("reasoning", "Models with thinking/reasoning support"),
            ("multipart", "Models that support images and files"),
            ("tools", "Models with tool/function calling support"),
            ("free", "Free models (no cost)")
        ]
        
        console.print("[bold magenta]Available Capabilities:[/bold magenta]")
        for i, (cap, desc) in enumerate(capabilities, 1):
            console.print(f"[bold]{i}.[/bold] {desc}")
        console.print("[bold]b[/bold] - Go back to main menu")
        
        cap_choice = Prompt.ask("Select a capability", choices=["1", "2", "3", "4", "b"], default="1")
        
        if cap_choice.lower() == 'b':
            return select_model(config)
        
        try:
            cap_index = int(cap_choice) - 1
            if 0 <= cap_index < len(capabilities):
                selected_capability, description = capabilities[cap_index]
                
                console.print(f"[cyan]Loading models with {description.lower()}...[/cyan]")
                try:
                    capability_models = get_models_by_capability(selected_capability)
                    
                    if not capability_models:
                        console.print(f"[yellow]No models found with {description.lower()}.[/yellow]")
                        Prompt.ask("Press Enter to continue")
                        return select_model(config)
                    
                    console.print(f"[bold green]{description}:[/bold green]")
                    console.print(f"[dim]Found {len(capability_models)} models[/dim]\n")
                    
                    for i, model in enumerate(capability_models, 1):
                        if model is None:
                            continue
                            
                        endpoint = model.get('endpoint', {}) if model else {}
                        model_name = model.get('slug') or model.get('name') or model.get('short_name', 'Unknown') if model else 'Unknown'
                        
                        extra_info = ""
                        if selected_capability == "reasoning":
                            reasoning_config = model.get('reasoning_config') or endpoint.get('reasoning_config') if model and endpoint else None
                            if reasoning_config:
                                start_token = reasoning_config.get('start_token', '<thinking>')
                                end_token = reasoning_config.get('end_token', '</thinking>')
                                extra_info = f" [dim]({start_token}...{end_token})[/dim]"
                        elif selected_capability == "multipart":
                            input_modalities = model.get('input_modalities', []) if model else []
                            if input_modalities:
                                extra_info = f" [dim]({', '.join(input_modalities)})[/dim]"
                        elif selected_capability == "tools":
                            supported_params = endpoint.get('supported_parameters', []) if endpoint else []
                            if supported_params is None:
                                supported_params = []
                            tool_params = [p for p in supported_params if 'tool' in p.lower()]
                            if tool_params:
                                extra_info = f" [dim]({', '.join(tool_params)})[/dim]"
                        elif selected_capability == "free":
                            provider = endpoint.get('provider_name', 'Unknown') if endpoint else 'Unknown'
                            extra_info = f" [green](FREE via {provider})[/green]"
                        
                        console.print(f"[bold]{i}.[/bold] {model_name}{extra_info}")
                    
                    console.print(f"\n[bold]b[/bold] - Go back to capability selection")
                    
                    model_choice = Prompt.ask("Enter model number or 'b' to go back", default="1")
                    
                    if model_choice.lower() == 'b':
                        return select_model(config)
                    
                    try:
                        model_index = int(model_choice) - 1
                        if 0 <= model_index < len(capability_models):
                            selected_model_obj = capability_models[model_index]
                            if selected_model_obj:
                                selected_model = selected_model_obj.get('slug') or selected_model_obj.get('name') or selected_model_obj.get('short_name', 'Unknown')
                            else:
                                selected_model = 'Unknown'
                            console.print(f"[green]Selected {selected_model} with {description.lower()}[/green]")
                            
                            try:
                                auto_detect_thinking_mode(config, selected_model)
                            except Exception as e:
                                console.print(f"[yellow]Error detecting thinking mode: {str(e)}. Using default settings.[/yellow]")
                            return selected_model
                        else:
                            console.print("[red]Invalid selection[/red]")
                            Prompt.ask("Press Enter to continue")
                            return select_model(config)
                    except ValueError:
                        console.print("[red]Please enter a valid number[/red]")
                        Prompt.ask("Press Enter to continue")
                        return select_model(config)
                        
                except Exception as e:
                    console.print(f"[red]Error loading capability models: {str(e)}[/red]")
                    console.print("[yellow]Falling back to standard model selection[/yellow]")
                    Prompt.ask("Press Enter to continue")
                    return select_model(config)
            else:
                console.print("[red]Invalid capability selection[/red]")
                return select_model(config)
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
            return select_model(config)

    elif choice == "6":
        # Browse models by groups using enhanced API
        console.print("[bold green]Browse Models by Groups:[/bold green]")
        console.print("[dim]Using enhanced OpenRouter frontend API data[/dim]\n")
        
        try:
            groups = get_models_by_group()
            
            if not groups:
                console.print("[yellow]No model groups found.[/yellow]")
                Prompt.ask("Press Enter to continue")
                return select_model(config)
            
            sorted_groups = sorted(groups.keys())
            console.print("[bold magenta]Available Model Groups:[/bold magenta]")
            for i, group in enumerate(sorted_groups, 1):
                model_count = len(groups[group])
                console.print(f"[bold]{i}.[/bold] {group} [dim]({model_count} models)[/dim]")
            console.print("[bold]b[/bold] - Go back to main menu")
            
            group_choice = Prompt.ask("Select a group", default="1")
            
            if group_choice.lower() == 'b':
                return select_model(config)
            
            try:
                group_index = int(group_choice) - 1
                if 0 <= group_index < len(sorted_groups):
                    selected_group = sorted_groups[group_index]
                    group_models = groups[selected_group]
                    
                    console.print(f"[bold green]{selected_group} Models:[/bold green]")
                    console.print(f"[dim]Found {len(group_models)} models in this group[/dim]\n")
                    
                    for i, model in enumerate(group_models, 1):
                        if model is None:
                            continue
                            
                        endpoint = model.get('endpoint', {}) if model else {}
                        model_name = model.get('slug') or model.get('name') or model.get('short_name', 'Unknown') if model else 'Unknown'
                        provider = endpoint.get('provider_name', 'Unknown') if endpoint else 'Unknown'
                        
                        pricing_info = ""
                        if endpoint and endpoint.get('is_free', False):
                            pricing_info = " [green](FREE)[/green]"
                        elif endpoint:
                            pricing = endpoint.get('pricing', {})
                            if pricing:
                                prompt_price = pricing.get('prompt', '0')
                                try:
                                    if float(prompt_price) > 0:
                                        pricing_info = f" [dim](${prompt_price}/token)[/dim]"
                                except:
                                    pass
                        
                        console.print(f"[bold]{i}.[/bold] {model_name} [dim]({provider})[/dim]{pricing_info}")
                    
                    console.print(f"\n[bold]b[/bold] - Go back to group selection")
                    
                    model_choice = Prompt.ask("Enter model number or 'b' to go back", default="1")
                    
                    if model_choice.lower() == 'b':
                        return select_model(config)
                    
                    try:
                        model_index = int(model_choice) - 1
                        if 0 <= model_index < len(group_models):
                            selected_model_obj = group_models[model_index]
                            if selected_model_obj:
                                selected_model = selected_model_obj.get('slug') or selected_model_obj.get('name') or selected_model_obj.get('short_name', 'Unknown')
                            else:
                                selected_model = 'Unknown'
                            console.print(f"[green]Selected {selected_model} from {selected_group} group[/green]")
                            
                            try:
                                auto_detect_thinking_mode(config, selected_model)
                            except Exception as e:
                                console.print(f"[yellow]Error detecting thinking mode: {str(e)}. Using default settings.[/yellow]")
                            return selected_model
                        else:
                            console.print("[red]Invalid selection[/red]")
                            Prompt.ask("Press Enter to continue")
                            return select_model(config)
                    except ValueError:
                        console.print("[red]Please enter a valid number[/red]")
                        Prompt.ask("Press Enter to continue")
                        return select_model(config)
                else:
                    console.print("[red]Invalid group selection[/red]")
                    return select_model(config)
            except ValueError:
                console.print("[red]Please enter a valid number[/red]")
                return select_model(config)
                
        except Exception as e:
            console.print(f"[red]Error loading model groups: {str(e)}[/red]")
            console.print("[yellow]Falling back to standard model selection[/yellow]")
            Prompt.ask("Press Enter to continue")
            return select_model(config)


def get_model_recommendations(task_type=None, budget=None):
    """Recommends models based on task type and budget constraints using dynamic OpenRouter categories"""
    all_models = get_available_models()

    if not task_type:
        return all_models

    # Get dynamic task categories from OpenRouter API instead of hardcoded ones
    try:
        task_categories = get_dynamic_task_categories()
        console.print(f"[dim]Using dynamic categories for task: {task_type}[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to get dynamic categories, using fallback patterns: {str(e)}[/yellow]")
        # Fallback to basic patterns if API fails
        task_categories = {
            "creative": ["claude-3", "gpt-4", "llama", "gemini"],
            "coding": ["claude-3-opus", "gpt-4", "deepseek-coder", "qwen-coder", "devstral", "codestral"],
            "analysis": ["claude-3-opus", "gpt-4", "mistral", "qwen"],
            "chat": ["claude-3-haiku", "gpt-3.5", "gemini-pro", "llama"]
        }

    recommended = []
    task_model_patterns = task_categories.get(task_type, [])
    
    for model in all_models:
        model_id = model.get('id', '').lower()
        # Check if model matches any of the task-specific patterns/slugs
        if any(pattern.lower() in model_id for pattern in task_model_patterns):
            # Filter by budget if specified
            if budget == "free" and ":free" in model['id']:
                recommended.append(model)
            elif budget is None or budget != "free":
                recommended.append(model)

    return recommended or all_models