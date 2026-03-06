```javascript
import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchDashboardConfig, updateDashboardConfig } from '../store/dashboardSlice';
import DashboardWidget from './DashboardWidget';
import DashboardConfig from './DashboardConfig';

const Dashboard = () => {
    const dispatch = useDispatch();
    const config = useSelector(state => state.dashboard.config);
    const [widgets, setWidgets] = useState(config.widgets || []);

    useEffect(() => {
        dispatch(fetchDashboardConfig());
    }, [dispatch]);

    const handleWidgetResize = (widgetId, newSize) => {
        const newWidgets = widgets.map(widget => {
            if (widget.id === widgetId) {
                return { ...widget, size: newSize };
            }
            return widget;
        });
        setWidgets(newWidgets);
        dispatch(updateDashboardConfig({ widgets: newWidgets }));
    };

    const handleWidgetReorder = (draggedWidget, targetIndex) => {
        const newWidgets = [...widgets];
        const draggedWidgetIndex = newWidgets.indexOf(draggedWidget);
        if (draggedWidgetIndex !== -1) {
            newWidgets.splice(targetIndex, 0, newWidgets.splice(draggedWidgetIndex, 1)[0]);
            setWidgets(newWidgets);
            dispatch(updateDashboardConfig({ widgets: newWidgets }));
        }
    };

    return (
        <div className="dashboard">
            <DashboardConfig widgets={widgets} onConfigChange={setWidgets} />
            <div className="widgets">
                {widgets.map(widget => (
                    <DashboardWidget
                        key={widget.id}
                        id={widget.id}
                        title={widget.title}
                        size={widget.size}
                        onResize={handleWidgetResize}
                        onReorder={handleWidgetReorder}
                    />
                ))}
            </div>
        </div>
    );
};

export default Dashboard;
```