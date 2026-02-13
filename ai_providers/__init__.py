# Copyright 2025 Frank Sommers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
AI Provider abstraction layer for document generation.

This package provides a unified interface for different AI providers
(Gemini, Novita, etc.) to generate documents and analyze images.
"""

from .base_provider import AIProvider, ProviderConfig
from .provider_factory import ProviderFactory, get_ai_client
from .gemini_provider import GeminiProvider
from .novita_provider import NovitaProvider

# Register available providers
ProviderFactory.register_provider('gemini', GeminiProvider)
ProviderFactory.register_provider('novita', NovitaProvider)

__all__ = [
    'AIProvider',
    'ProviderConfig',
    'ProviderFactory',
    'get_ai_client',
    'GeminiProvider',
    'NovitaProvider'
]
