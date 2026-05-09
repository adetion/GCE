#
# -*- coding: utf-8 -*-
#
#
# Gaming Chaos Engine V0.1.0 – A chaos engine for gaming and simulation
# Copyright (C) 2026  Adetion
# All rights reserved.
#
# Contact:
#   Email: i126@126.com
#   Website: wop.cc
#
# LICENSE TERMS
# =============
# This software and associated documentation files (the "Software") are
# proprietary and protected by copyright law. The copyright holder
# grants you a limited, non-exclusive, non-transferable license to use,
# copy, and modify the Software solely for non-commercial, personal
# purposes, subject to the following conditions:
#
# 1. You must retain the above copyright notice, this list of conditions,
#    and the following disclaimer in all copies or substantial portions
#    of the Software.
# 2. You may not use the Software, or any derivative works based upon it,
#    for any commercial purpose without obtaining a separate commercial
#    license from the copyright holder.
# 3. Redistribution of the Software or derivative works, whether in
#    source or binary form, is prohibited without prior written
#    permission, except as part of non-commercial personal use.
#
# "Commercial purpose" includes, but is not limited to: using the
# Software (a) in any product or service sold or made available for a
# fee; (b) as part of any commercial activity intended to generate
# revenue, including internal business operations; (c) by any entity
# that is a for-profit organization or operates in a commercial context.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
# OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# For commercial licensing inquiries, please contact:
#   Email: i126@126.com
#   Website: wop.cc
#
# ─────────────────────────────────────
#
# 博弈混沌引擎 V0.1.0 – 用于博弈与仿真的混沌引擎
# 版权所有 (C) 2026  Adetion
# 保留所有权利。
#
# 联系方式：
#   邮箱：i126@126.com
#   网站：wop.cc
#
# 许可条款
# ========
# 本软件及相关文档（以下简称"软件"）为专有软件，受版权法保护。
# 版权持有人授予您一项有限的、非排他的、不可转让的许可，允许您
# 仅为个人非商业目的使用、复制和修改本软件，但必须遵守以下条件：
#
# 1. 您必须在软件的所有副本或重要部分中保留上述版权声明、本条件
#    列表以及随附的免责声明。
# 2. 未经版权持有人事先书面授权，您不得将本软件或其衍生作品用于
#    任何商业目的。如需商用，必须单独获得商用许可。
# 3. 除个人非商业使用场景外，禁止以源代码或二进制形式再分发本软件
#    或其衍生作品，除非事先获得书面许可。
#
# "商业目的"包括但不限于：(a) 将软件用于任何收费产品或服务中；
# (b) 作为任何以营利或产生收入为目的的商业活动的一部分，包括内部
# 业务运营；(c) 由营利性实体或在商业环境中运营的实体使用。
#
# 本软件按"原样"提供，不提供任何明示或暗示的保证，包括但不限于
# 对适销性、特定目的适用性和非侵权的保证。在任何情况下，版权
# 持有人均不对因使用或无法使用本软件而产生的任何索赔、损害或
# 其他责任负责，无论是合同、侵权还是其他方面。
#
# 如需获取商业许可，请联系：
#   邮箱：i126@126.com
#   网站：wop.cc

"""事件总线 (multiprocessing.Queue 封装) 测试 / Event bus (multiprocessing.Queue wrapper) tests."""

from __future__ import annotations

import multiprocessing
import time

import pytest

from gce.environment.GCE_base import GCE_EventType, GCE_RawEvent
from gce.environment.GCE_event_bus import GCE_EventBus


def GCE__make_event(
    source_id: str = "test-source",
    event_type: GCE_EventType = GCE_EventType.NUMERIC,
    timestamp: int | None = None,
    value: float | None = 1.0,
) -> GCE_RawEvent:
    if timestamp is None:
        timestamp = int(time.time() * 1000)
    return GCE_RawEvent(
        source_id=source_id,
        event_type=event_type,
        timestamp=timestamp,
        value=value,
    )


class GCE_TestEventBusCreation:

    def GCE_test_create_with_default_maxsize(self):
        bus = GCE_EventBus()
        assert bus is not None
        assert bus.GCE_queue is not None
        bus.GCE_close()

    def GCE_test_create_with_custom_maxsize(self):
        bus = GCE_EventBus(maxsize=50)
        assert bus is not None
        assert bus.GCE_queue is not None
        bus.GCE_close()

    def GCE_test_gce_queue_property_returns_multiprocessing_queue(self):
        bus = GCE_EventBus(maxsize=10)
        try:
            q = bus.GCE_queue
            assert isinstance(q, multiprocessing.queues.Queue)
        finally:
            bus.GCE_close()


class GCE_TestEventBusPublishConsume:

    def GCE_test_publish_consume_roundtrip(self):
        bus = GCE_EventBus()
        try:
            event = GCE__make_event(source_id="sensor-1", value=3.14)
            ok = bus.GCE_publish(event)
            assert ok
            consumed = bus.GCE_consume(timeout=1.0)
            assert consumed is not None
            assert consumed.source_id == "sensor-1"
            assert consumed.value == pytest.approx(3.14)
            assert consumed.event_type == GCE_EventType.NUMERIC
        finally:
            bus.GCE_close()

    def GCE_test_publish_consume_text_event(self):
        bus = GCE_EventBus()
        try:
            event = GCE_RawEvent(
                source_id="text-source",
                event_type=GCE_EventType.TEXT,
                timestamp=int(time.time() * 1000),
                text="hello world",
            )
            ok = bus.GCE_publish(event)
            assert ok
            consumed = bus.GCE_consume(timeout=1.0)
            assert consumed is not None
            assert consumed.source_id == "text-source"
            assert consumed.event_type == GCE_EventType.TEXT
            assert consumed.text == "hello world"
        finally:
            bus.GCE_close()

    def GCE_test_consume_empty_queue_returns_none(self):
        bus = GCE_EventBus()
        try:
            # Queue is empty — consume should time out and return None
            result = bus.GCE_consume(timeout=0.01)
            assert result is None
        finally:
            bus.GCE_close()


class GCE_TestEventBusFull:

    def GCE_test_publish_returns_false_when_queue_full(self):
        bus = GCE_EventBus(maxsize=1)
        try:
            event1 = GCE__make_event(source_id="first", value=10.0)
            ok1 = bus.GCE_publish(event1, timeout=0.1)
            assert ok1

            event2 = GCE__make_event(source_id="second", value=20.0)
            # Queue is full (maxsize=1), publish should return False
            ok2 = bus.GCE_publish(event2, timeout=0.01)
            assert not ok2

            # After consuming the first, should be able to publish again
            consumed = bus.GCE_consume(timeout=0.1)
            assert consumed is not None
            assert consumed.source_id == "first"

            ok3 = bus.GCE_publish(event2, timeout=0.1)
            assert ok3
        finally:
            bus.GCE_close()


class GCE_TestEventBusFifo:

    def GCE_test_multiple_events_fifo_order(self):
        bus = GCE_EventBus(maxsize=100)
        try:
            e1 = GCE__make_event(source_id="e1", value=1.0)
            e2 = GCE__make_event(source_id="e2", value=2.0)
            e3 = GCE__make_event(source_id="e3", value=3.0)

            bus.GCE_publish(e1)
            bus.GCE_publish(e2)
            bus.GCE_publish(e3)

            r1 = bus.GCE_consume(timeout=1.0)
            r2 = bus.GCE_consume(timeout=1.0)
            r3 = bus.GCE_consume(timeout=1.0)

            assert r1 is not None and r1.source_id == "e1"
            assert r2 is not None and r2.source_id == "e2"
            assert r3 is not None and r3.source_id == "e3"
        finally:
            bus.GCE_close()


class GCE_TestEventBusClose:

    def GCE_test_close_works_without_error(self):
        bus = GCE_EventBus()
        # close should not raise
        bus.GCE_close()

    def GCE_test_close_after_publish_consume(self):
        bus = GCE_EventBus()
        event = GCE__make_event(value=42.0)
        bus.GCE_publish(event)
        _ = bus.GCE_consume(timeout=1.0)
        bus.GCE_close()  # should not raise

    def GCE_test_double_close_does_not_crash(self):
        bus = GCE_EventBus()
        bus.GCE_close()
        # Second close should not raise an error
        bus.GCE_close()


class GCE_TestRawEventImmutability:

    def GCE_test_raw_event_is_frozen(self):
        event = GCE__make_event(source_id="immutable", value=5.0)
        assert event.source_id == "immutable"
        assert event.value == pytest.approx(5.0)
        # frozen dataclass — mutation should fail
        with pytest.raises(Exception):
            event.source_id = "mutated"  # type: ignore[misc]

    def GCE_test_raw_event_defaults(self):
        ts = int(time.time() * 1000)
        event = GCE_RawEvent(
            source_id="minimal",
            event_type=GCE_EventType.NUMERIC,
            timestamp=ts,
        )
        assert event.value is None
        assert event.text is None
        assert event.vector is None
        assert event.metadata == {}
