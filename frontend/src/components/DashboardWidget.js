```javascript
import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { updateDashboardConfig } from '../store/dashboardSlice';

const DashboardWidget = ({ id, title, size, onResize, onReorder }) => {
    const dispatch = useDispatch();
    const [isDragging, setIsDragging] = useState(false);

    const handleResize = (newSize) => {
        onResize(id, newSize);
    };

    return (
        <div
            className="widget"
            style={{ width: `${size}px` }}
            onDragStart={() => setIsDragging(true)}
            onDragEnd={() => setIsDragging(false)}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
                e.preventDefault();
                const targetIndex = e.target.closest('.widget').dataset.index;
                onReorder({ id, size }, targetIndex);
            }}
        >
            <div className="widget-header">
                <span>{title}</span>
                <div className="widget-controls">
                    <button onClick={() => handleResize(size + 10)}>+</button>
                    <button onClick={() => handleResize(size - 10)}>-</button>
                </div>
            </div>
            <div className="widget-content">
                {/* Widget content */}
            </div>
        </div>
    );
};

export default DashboardWidget;
```