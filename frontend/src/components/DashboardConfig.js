```javascript
import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { updateDashboardConfig } from '../store/dashboardSlice';

const DashboardConfig = ({ widgets, onConfigChange }) => {
    const dispatch = useDispatch();

    const handleWidgetOrderChange = (order) => {
        const newWidgets = widgets.map((widget, index) => ({ ...widget, order }));
        onConfigChange(newWidgets);
        dispatch(updateDashboardConfig({ widgets: newWidgets }));
    };

    return (
        <div className="dashboard-config">
            <div className="config-header">
                <h2>Dashboard Configuration</h2>
            </div>
            <div className="config-widgets">
                {widgets.map((widget, index) => (
                    <div
                        key={widget.id}
                        className="config-widget"
                        data-index={index}
                    >
                        <span>{widget.title}</span>
                        <button onClick={() => handleWidgetOrderChange(index)}>Reorder</button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default DashboardConfig;
```