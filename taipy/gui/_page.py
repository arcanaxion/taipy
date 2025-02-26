# Copyright 2021-2025 Avaiga Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

# _Page for multipage support
from __future__ import annotations

import logging
import re
import typing as t
import warnings
from pathlib import Path

from ._warnings import TaipyGuiAlwaysWarning

if t.TYPE_CHECKING:
    from ._renderers import Page
    from .gui import Gui

_DETECT_CLOSING_TAGS = re.compile(r"<([A-Z][-\w]*)(([^>\"]+\"[^\"]*\")*\s*)?(><\/\1>)", flags=re.MULTILINE)
_SUBSTR_CLOSING_TAG = "<\\1\\2/>"


class _Page(object):
    def __init__(self) -> None:
        self._rendered_jsx: t.Optional[str] = None
        self._renderer: t.Optional[Page] = None
        self._style: t.Optional[t.Union[str, t.Dict[str, t.Any]]] = None
        self._route: t.Optional[str] = None
        self._head: t.Optional[list] = None
        self._script_paths: t.Optional[t.Union[str, Path, t.List[t.Union[str, Path]]]] = None

    def render(self, gui: Gui, silent: t.Optional[bool] = False):
        if self._renderer is None:
            raise RuntimeError(f"Can't render page {self._route}: no renderer found")
        with warnings.catch_warnings(record=True) as w:
            warnings.resetwarnings()
            module_name = self._renderer._get_module_name()
            with gui._set_locals_context(module_name):
                render_return = self._renderer.render(gui)
                if isinstance(render_return, tuple):
                    self._rendered_jsx, module_name = render_return
                else:
                    self._rendered_jsx = render_return
            if silent:
                s = ""
                for wm in w:
                    if wm.category is TaipyGuiAlwaysWarning:
                        s += f" - {wm.message}\n"
                if s:
                    logging.warning("\033[1;31m\n" + s)

            else:
                if (
                    self._rendered_jsx
                    and isinstance(self._rendered_jsx, str)
                    and (
                        result := _DETECT_CLOSING_TAGS.sub(
                            _SUBSTR_CLOSING_TAG,
                            self._rendered_jsx.replace(">style</TaipyStyle>", "/>"),
                        )
                    )
                ):
                    self._rendered_jsx = result
                if w:
                    s = "\033[1;31m\n"
                    s += (
                        message
                        := f"--- {len(w)} warning(s) were found for page '{'/' if self._route == gui._get_root_page_name() else self._route}' {self._renderer._get_content_detail(gui)} ---\n"  # noqa: E501
                    )
                    for i, wm in enumerate(w):
                        s += f" - Warning {i + 1}: {wm.message}\n"
                    s += "-" * len(message)
                    s += "\033[0m\n"
                    logging.warning(s)
        if hasattr(self._renderer, "head"):
            self._head = list(self._renderer.head)  # type: ignore
        # return renderer module_name from frame
        return module_name
