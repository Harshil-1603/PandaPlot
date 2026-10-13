"""Project insertion stays in the nearest valid parent collection."""

import pytest

from pandaplot.models.project import Project
from pandaplot.models.project.items import Item, ItemCollection
from pandaplot.models.project.items.chart import Chart
from pandaplot.models.project.items.folder import Folder


def test_chart_parent_uses_its_nested_folder() -> None:
    project = Project()
    outer = Folder(name="Outer")
    folder = Folder(name="Inner")
    chart = Chart(name="Chart")
    project.add_item(outer)
    project.add_item(folder, parent_id=outer.id)
    project.add_item(chart, parent_id=folder.id)
    item = Item(name="New item")

    project.add_item(item, parent_id=chart.id, index=0)

    assert folder.get_items() == [item, chart]
    assert item.parent_id == folder.id
    assert item not in project.root.get_items()
    assert project.find_item(item.id) is item


def test_non_collection_parent_chain_uses_nearest_collection() -> None:
    project = Project()
    folder = Folder()
    first = Item()
    second = Item()
    project.add_item(folder)
    project.add_item(first, parent_id=folder.id)
    project.add_item(second)
    second.parent_id = first.id
    subtree = ItemCollection()
    child = Item()
    subtree.add_item(child)

    project.add_item(subtree, parent_id=second.id)

    assert subtree.parent_id == folder.id
    assert folder.get_items() == [first, subtree]
    assert project.find_item(child.id) is child
    assert child.parent_id == subtree.id


@pytest.mark.parametrize("parent_kind", ["missing", "root_child", "dangling", "cycle"])
def test_unresolvable_parent_falls_back_to_root(parent_kind: str) -> None:
    project = Project()
    parent = Item()
    project.add_item(parent)
    if parent_kind == "missing":
        parent_id = "unknown"
    else:
        parent_id = parent.id
        if parent_kind == "dangling":
            parent.parent_id = "unknown"
        elif parent_kind == "cycle":
            other = Item()
            project.add_item(other)
            parent.parent_id = other.id
            other.parent_id = parent.id
    item = Item()

    project.add_item(item, parent_id=parent_id, index=0)

    assert item.parent_id == project.root.id
    assert project.root.get_items()[0] is item
    assert project.find_item(item.id) is item


def test_inferred_parent_cannot_attach_a_folder_to_itself() -> None:
    project = Project()
    folder = Folder()
    chart = Chart()
    project.add_item(folder)
    project.add_item(chart, parent_id=folder.id)
    original_root_items = project.root.get_items()

    with pytest.raises(ValueError, match="itself or its descendants"):
        project.add_item(folder, parent_id=chart.id)

    assert project.root.get_items() == original_root_items
    assert folder.get_items() == [chart]
    assert folder.parent_id == project.root.id
