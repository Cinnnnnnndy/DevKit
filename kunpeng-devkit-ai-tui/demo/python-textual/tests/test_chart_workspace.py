"""Interaction checks for the launch and chart workspace."""

from __future__ import annotations

from unittest import IsolatedAsyncioTestCase

from textual.widgets import Input, TabbedContent, Tabs

from devkitai import DevKitAI, FlameGraph, HalftoneField, OperatorTable, PROFILE, TimeSeriesChart, TraceLanes, WorkerTable


class ChartWorkspaceTest(IsolatedAsyncioTestCase):
    async def test_chart_command_opens_workspace_and_escape_returns(self) -> None:
        app = DevKitAI()
        async with app.run_test(size=(156, 48)) as pilot:
            task_input = app.query_one("#task-input", Input)
            task_input.value = "/chart"
            await pilot.press("enter")
            await pilot.pause()

            self.assertTrue(app.query_one("#launch").has_class("hidden"))
            self.assertFalse(app.query_one("#chart-workspace").has_class("hidden"))
            self.assertEqual(app.query_one("#chart-tabs", TabbedContent).active, "overview")
            self.assertFalse(app.query_one(HalftoneField)._animation_timer._active.is_set())

            for pane in ("cpu", "numa", "flame", "trace", "operators"):
                await pilot.press("right")
                await pilot.pause()
                self.assertEqual(app.query_one("#chart-tabs", TabbedContent).active, pane)

            await pilot.press("escape")
            await pilot.pause()

            self.assertFalse(app.query_one("#launch").has_class("hidden"))
            self.assertTrue(app.query_one("#chart-workspace").has_class("hidden"))
            self.assertEqual(task_input.value, "")
            self.assertTrue(app.query_one(HalftoneField)._animation_timer._active.is_set())

    async def test_chart_cursor_pause_and_object_selection_are_interactive(self) -> None:
        app = DevKitAI()
        async with app.run_test(size=(156, 48)) as pilot:
            app.open_chart_workspace()
            tabs = app.query_one("#chart-tabs", TabbedContent)

            chart = app.query_one(TimeSeriesChart)
            chart.focus()
            PROFILE.cursor_index = 10
            await pilot.press("right")
            self.assertEqual(PROFILE.cursor_index, 11)
            self.assertTrue(PROFILE.cursor_locked)

            await pilot.press("space")
            self.assertTrue(PROFILE.paused)
            await pilot.press("space")
            self.assertFalse(PROFILE.paused)

            tabs.query_one(Tabs).focus()
            tabs.active = "flame"
            flame = app.query_one(FlameGraph)
            flame.focus()
            previous_frame = PROFILE.selected_flame
            await pilot.press("down")
            self.assertEqual(PROFILE.selected_flame, min(len(PROFILE.flame_nodes) - 1, previous_frame + 1))

            tabs.active = "operators"
            operators = app.query_one(OperatorTable)
            operators.focus()
            previous_operator = PROFILE.selected_operator
            await pilot.press("down")
            self.assertEqual(PROFILE.selected_operator, (previous_operator + 1) % len(PROFILE.operators))

            tabs.active = "trace"
            trace = app.query_one(TraceLanes)
            trace.focus()
            previous_lane = PROFILE.selected_span
            await pilot.press("down")
            self.assertEqual(PROFILE.selected_span, (previous_lane + 1) % len(PROFILE.trace_lanes))

            tabs.active = "cpu"
            worker_table = app.query_one("#cpu").query_one(WorkerTable)
            worker_table.focus()
            previous_worker = PROFILE.selected_worker
            await pilot.press("down")
            self.assertEqual(PROFILE.selected_worker, (previous_worker + 1) % len(PROFILE.workers))

    def test_detail_views_have_instance_level_density(self) -> None:
        self.assertGreaterEqual(len(PROFILE.trace_lanes), 28)
        self.assertGreaterEqual(len(PROFILE.flame_nodes), 18)
        self.assertGreaterEqual(len(PROFILE.operators), 16)
        self.assertGreaterEqual(len(PROFILE.workers), 32)
        worker_27 = PROFILE.workers[27]
        self.assertEqual((worker_27.cpu, worker_27.numa), (36, 2))
        self.assertTrue(any(lane.name == "worker-27" for lane in PROFILE.trace_lanes))
        self.assertGreaterEqual(max(node.depth for node in PROFILE.flame_nodes), 8)
        self.assertGreaterEqual(len({node.depth for node in PROFILE.flame_nodes}), 9)
        for depth in {node.depth for node in PROFILE.flame_nodes}:
            row = sorted((node.start, node.start + node.percent) for node in PROFILE.flame_nodes if node.depth == depth)
            self.assertTrue(all(left[1] <= right[0] for left, right in zip(row, row[1:])))
        skyline_depths = []
        for column in range(100):
            active = [node.depth for node in PROFILE.flame_nodes if node.start <= column < node.start + node.percent]
            skyline_depths.append(max(active, default=0))
        self.assertGreaterEqual(len(set(skyline_depths)), 6)
        self.assertGreaterEqual(max(skyline_depths) - min(skyline_depths), 8)
        flame_thicknesses = [3 if node.self_ms >= 12 else 2 if node.self_ms >= 4 else 1 for node in PROFILE.flame_nodes]
        self.assertEqual(set(flame_thicknesses), {1, 2, 3})
