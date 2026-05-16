import typing
import io
import datetime

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from matplotlib.axes import Axes


class Plot:
    """
    Data container for a single plot line

    Attributes:
        x: X-axis coordinates
        y: Y-axis coordinates
        label: text label for the plot line
        annotation_way: optional callback for adding label relatively the plot
    """
    def __init__(
        self,
        /,
        x: typing.Iterable[float | int],
        y: typing.Iterable[float | int],
        label: str,
        annotation_way: typing.Optional[typing.Callable] = None,
    ):
        self.x: tuple = tuple(x)
        self.y: tuple = tuple(y)
        self.label = label
        self.annotation_way = annotation_way


def figure(
    *,
    plots: typing.Iterable[Plot],
    x_label: str="",
    y_label: str="",
    figsize: tuple[float, float]=(12, 8),
) -> Figure:
    fig, ax = plt.subplots(figsize=figsize)

    for plot in plots:
        ax.plot(plot.x, plot.y)
        if plot.annotation_way:
            plot.annotation_way(ax=ax, label=plot.label, x=plot.x, y=plot.y)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    formatter = DateFormatter("%d %b %Y") # %b - Month, %Y - Year (https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior)
    ax.xaxis.set_major_formatter(formatter)
    ax.tick_params(axis='x', labelrotation=25)

    return fig


def annotate_as_date(
    *,
    ax: Axes,
    label: str,
    x: typing.Sequence[typing.Any],
    y: typing.Sequence[typing.Any],
):
    ax.annotate(
        label,
        xy=(x[-1] + (x[-1] - x[-2]), y[-1]),
        arrowprops=dict(arrowstyle="->")
    )


def alltime_figure(grouped_statistic_by_nickname: dict[str, list], stored_obj: str | io.BytesIO):
    # build the plot
    plots = []
    for group in grouped_statistic_by_nickname:
        s = grouped_statistic_by_nickname[group]
        plots.append(
            Plot(
                x=[datetime.datetime(i.year, i.month, i.day) for i in s], # type: ignore
                y=[i.alltime // 1024 // 1024 // 1024 for i in s],
                label=group,
                annotation_way=annotate_as_date,
            )
        )

    # show the plot
    plt.style.use("ggplot")
    fig = figure(
        plots=plots,
        x_label="Date",
        y_label="Gigabytes",
    )
    fig.savefig(stored_obj)


def diff_figure(grouped_statistic_by_nickname: dict[str, list], stored_obj: str | io.BytesIO):
    # build the plot
    plots = []
    for group in grouped_statistic_by_nickname:
        s = grouped_statistic_by_nickname[group]
        plots.append(
            Plot(
                x=[datetime.datetime(i.year, i.month, i.day) for i in s[1:]], # type: ignore
                y=[(s[i].alltime - s[i-1].alltime) // 1024 // 1024 // 1024 for i in range(1, len(s))],
                label=group,
                annotation_way=annotate_as_date,
            )
        )

    # show the plot
    plt.style.use("ggplot")
    fig = figure(
        plots=plots,
        x_label="Date",
        y_label="Gigabytes",
    )
    plt.savefig(stored_obj)



if __name__ == '__main__':
    import numpy as np

    greg_plot = Plot(
        x=range(10),
        y=range(10),
        label="gregory",
        annotation_way=annotate_as_date,
    )
    dima_plot = Plot(
        x=np.linspace(0, 10, 100),
        y=0.5 + 0.5 * np.sin(0.5 * np.linspace(0, 10, 100)),
        label="dmitriy",
        annotation_way=annotate_as_date,
    )
    
    plt.style.use("ggplot")
    fig = figure(plots=[greg_plot, dima_plot])
    plt.show()
    
    # fig.savefig("sword_art_online")
    # print(help(fig))